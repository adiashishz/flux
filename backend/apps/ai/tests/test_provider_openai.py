import json
from types import SimpleNamespace

import httpx
import openai
import pytest

from apps.ai.services.planning import WeekPlan
from apps.ai.services.providers.base import LLMError, StructuredOutputError, ToolCall
from apps.ai.services.providers.openai_compat import (
    OpenAICompatProvider,
    parse_json_text,
    to_openai_messages,
    to_openai_tools,
)

REQUEST = httpx.Request("POST", "https://example.test/v1/chat/completions")
TOOL = {"name": "create_card", "description": "Create a card", "input_schema": {"type": "object", "properties": {}}}


# ---- fakes ----------------------------------------------------------------------------------


def fragment(index=None, id=None, name=None, arguments=None):
    return SimpleNamespace(index=index, id=id, function=SimpleNamespace(name=name, arguments=arguments))


def chunk(content=None, tool_calls=None, finish=None, usage=None, choices=True):
    delta = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta, finish_reason=finish)] if choices else [], usage=usage)


def usage(prompt, completion):
    return SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion)


def reply(text, prompt=5, completion=7):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))], usage=usage(prompt, completion))


class FakeOpenAI:
    """Each script entry answers one create() call: a list of chunks (streamed), a reply, or an exception."""

    def __init__(self, *script):
        self.script, self.calls = list(script), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        entry = self.script.pop(0)
        if isinstance(entry, Exception):
            raise entry
        return iter(entry) if isinstance(entry, list) else entry


@pytest.fixture
def make(monkeypatch):
    def build(*script, name="gemini"):
        provider = OpenAICompatProvider(name, "https://example.test/v1", "key", "model-x")
        client = FakeOpenAI(*script)
        monkeypatch.setattr(provider, "_client", lambda: client)
        return provider, client

    return build


def run_turn(provider, tools=()):
    pieces = list(provider.stream_turn(system="sys", messages=[{"role": "user", "content": "hi"}], tools=list(tools)))
    return [p for kind, p in pieces if kind == "text"], [p for kind, p in pieces if kind == "turn"][0]


def http_error(cls, status, message="bad thing"):
    return cls(message, response=httpx.Response(status, request=REQUEST), body=None)


# ---- message and tool conversion ---------------------------------------------------------------


def test_plain_turns_pass_through_with_the_system_prompt_first():
    out = to_openai_messages("sys", [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}])
    assert out == [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]


def test_tool_use_blocks_become_tool_calls_with_json_string_arguments():
    out = to_openai_messages(
        "s",
        [{"role": "assistant", "content": [
            {"type": "text", "text": "On it."},
            {"type": "tool_use", "id": "t1", "name": "create_card", "input": {"title": "A"}},
        ]}],
    )
    assert out[1] == {
        "role": "assistant",
        "content": "On it.",
        "tool_calls": [{"id": "t1", "type": "function", "function": {"name": "create_card", "arguments": '{"title": "A"}'}}],
    }


def test_an_assistant_turn_with_only_tool_calls_has_null_content():
    out = to_openai_messages("s", [{"role": "assistant", "content": [{"type": "tool_use", "id": "t", "name": "n", "input": {}}]}])
    assert out[1]["content"] is None


def test_tool_results_become_tool_messages_and_errors_are_prefixed():
    out = to_openai_messages(
        "s",
        [{"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "a", "content": "{\"ok\": 1}", "is_error": False},
            {"type": "tool_result", "tool_use_id": "b", "content": "nope", "is_error": True},
        ]}],
    )
    assert out[1:] == [
        {"role": "tool", "tool_call_id": "a", "content": "{\"ok\": 1}"},
        {"role": "tool", "tool_call_id": "b", "content": "Error: nope"},
    ]


def test_tool_definitions_use_the_parameters_key():
    assert to_openai_tools([TOOL]) == [
        {"type": "function", "function": {"name": "create_card", "description": "Create a card", "parameters": TOOL["input_schema"]}}
    ]


# ---- streaming ---------------------------------------------------------------------------------


def test_text_streams_and_a_missing_usage_is_zero(make):
    provider, _ = make([chunk("Hel"), chunk("lo"), chunk(finish="stop")])
    texts, turn = run_turn(provider)
    assert texts == ["Hel", "lo"] and turn.text == "Hello"
    assert (turn.stop_reason, turn.usage) == ("end_turn", {"input_tokens": 0, "output_tokens": 0})


def test_a_tool_call_split_across_chunks_is_assembled(make):
    provider, _ = make([
        chunk(tool_calls=[fragment(0, "c1", "create_card", '{"title"')]),
        chunk(tool_calls=[fragment(0, None, None, ': "Ship"}')]),
        chunk(finish="tool_calls"),
    ])
    _, turn = run_turn(provider, [TOOL])
    assert turn.tool_calls == [ToolCall("c1", "create_card", {"title": "Ship"})] and turn.stop_reason == "tool_use"


def test_two_parallel_calls_are_kept_apart_by_index(make):
    provider, _ = make([
        chunk(tool_calls=[fragment(0, "a", "get_board", '{"board_id": "1"}'), fragment(1, "b", "get_board", '{"board_id": "2"}')]),
        chunk(finish="tool_calls"),
    ])
    _, turn = run_turn(provider)
    assert [c.arguments["board_id"] for c in turn.tool_calls] == ["1", "2"]


def test_fragments_without_an_index_are_matched_by_id_or_continue_the_last_call(make):
    provider, _ = make([
        chunk(tool_calls=[fragment(None, "a", "get_board", '{"board_')]),
        chunk(tool_calls=[fragment(None, None, None, 'id": "1"}')]),
        chunk(tool_calls=[fragment(None, "b", "list_boards", "{}")]),
        chunk(finish="tool_calls"),
    ])
    _, turn = run_turn(provider)
    assert [(c.id, c.name, c.arguments) for c in turn.tool_calls] == [
        ("a", "get_board", {"board_id": "1"}),
        ("b", "list_boards", {}),
    ]


def test_a_call_without_an_id_gets_one(make):
    provider, _ = make([chunk(tool_calls=[fragment(0, None, "list_boards", "")]), chunk(finish="tool_calls")])
    _, turn = run_turn(provider)
    assert turn.tool_calls == [ToolCall("call_1", "list_boards", {})]


def test_malformed_argument_json_is_flagged_for_the_model_to_fix(make):
    provider, _ = make([chunk(tool_calls=[fragment(0, "c", "create_card", '{"title": "unterminated')]), chunk(finish="tool_calls")])
    _, turn = run_turn(provider)
    call = turn.tool_calls[0]
    assert call.arguments == {} and "not valid JSON" in call.error


def test_arguments_that_are_not_an_object_are_flagged(make):
    provider, _ = make([chunk(tool_calls=[fragment(0, "c", "create_card", "[1, 2]")]), chunk(finish="tool_calls")])
    assert "JSON object" in run_turn(provider)[1].tool_calls[0].error


@pytest.mark.parametrize(
    "finish,with_call,expected",
    [
        ("tool_calls", True, "tool_use"),
        ("stop", True, "tool_use"),  # some servers say stop even though they asked for a tool
        (None, True, "tool_use"),  # and some never send a finish reason
        ("stop", False, "end_turn"),
        (None, False, "end_turn"),
        ("length", False, "max_tokens"),
        ("content_filter", False, "refusal"),
    ],
)
def test_finish_reasons_are_normalised(make, finish, with_call, expected):
    pieces = [chunk(tool_calls=[fragment(0, "c", "list_boards", "{}")])] if with_call else [chunk("x")]
    provider, _ = make(pieces + [chunk(finish=finish)])
    assert run_turn(provider)[1].stop_reason == expected


def test_usage_from_the_final_chunk_is_used(make):
    provider, _ = make([chunk("x"), chunk(choices=False, usage=usage(11, 4))])
    assert run_turn(provider)[1].usage == {"input_tokens": 11, "output_tokens": 4}


def test_the_request_has_the_model_stream_flag_and_tools_only_when_given(make, settings):
    settings.AI_MAX_TOKENS = 99
    settings.AI_STREAM_USAGE = False
    provider, client = make([chunk("a")], [chunk("b")])
    run_turn(provider)
    run_turn(provider, [TOOL])
    plain, with_tools = client.calls
    assert (plain["model"], plain["max_tokens"], plain["stream"]) == ("model-x", 99, True)
    assert "tools" not in plain and "stream_options" not in plain
    assert with_tools["tools"][0]["function"]["name"] == "create_card"


def test_stream_options_are_only_sent_when_enabled(make, settings):
    settings.AI_STREAM_USAGE = True
    provider, client = make([chunk("a")])
    run_turn(provider)
    assert client.calls[0]["stream_options"] == {"include_usage": True}


# ---- errors ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "error,name,expected",
    [
        (http_error(openai.AuthenticationError, 401), "gemini", "gemini rejected the API key."),
        (http_error(openai.RateLimitError, 429), "gemini", "rate limiting"),
        (openai.APIConnectionError(request=REQUEST), "ollama", "Is Ollama running"),
        (openai.APIConnectionError(request=REQUEST), "gemini", "Could not reach gemini at https://example.test/v1."),
        (http_error(openai.NotFoundError, 404), "groq", "does not know the model 'model-x'"),
        (http_error(openai.BadRequestError, 400, "model does not support tools"), "groq", "model does not support tools"),
        (http_error(openai.InternalServerError, 500), "groq", "returned an error"),
    ],
)
def test_vendor_errors_become_readable_llm_errors(make, error, name, expected):
    provider, _ = make(error, name=name)
    with pytest.raises(LLMError, match=expected):
        run_turn(provider)


def test_an_error_in_the_middle_of_a_stream_is_mapped_too(make):
    def broken():
        yield chunk("partial")
        raise http_error(openai.RateLimitError, 429)

    provider, client = make(name="gemini")
    client.script = [broken()]
    with pytest.raises(LLMError, match="rate limiting"):
        run_turn(provider)


def test_a_long_bad_request_message_is_trimmed(make):
    provider, _ = make(http_error(openai.BadRequestError, 400, "x" * 500))
    with pytest.raises(LLMError) as caught:
        run_turn(provider)
    assert len(str(caught.value)) < 260


# ---- structured output -------------------------------------------------------------------------

PLAN = {"summary": "A good week.", "items": [{"card_id": "c1", "day": "Monday", "reason": "Urgent."}]}


def test_json_schema_mode_is_tried_first_and_usage_is_summed(make):
    provider, client = make(reply(json.dumps(PLAN), 10, 20))
    plan, used = provider.structured(system="sys", messages=[{"role": "user", "content": "plan"}], output_model=WeekPlan)
    assert plan.summary == "A good week." and used == {"input_tokens": 10, "output_tokens": 20}
    assert client.calls[0]["response_format"]["type"] == "json_schema"
    assert client.calls[0]["response_format"]["json_schema"]["name"] == "WeekPlan"


def test_it_falls_back_to_json_object_mode_with_the_schema_in_the_prompt(make):
    provider, client = make(http_error(openai.BadRequestError, 400, "response_format unsupported"), reply(json.dumps(PLAN)))
    plan, _ = provider.structured(system="sys", messages=[], output_model=WeekPlan)
    assert plan.items[0].card_id == "c1"
    second = client.calls[1]
    assert second["response_format"] == {"type": "json_object"}
    system_prompt = second["messages"][0]["content"]
    assert "JSON schema" in system_prompt and '"summary"' in system_prompt


def test_json_in_a_code_fence_or_inside_prose_is_accepted(make):
    provider, _ = make(reply("```json\n" + json.dumps(PLAN) + "\n```"), reply("Here you go: " + json.dumps(PLAN) + " Hope it helps!"))
    assert provider.structured(system="s", messages=[], output_model=WeekPlan)[0].summary
    assert provider.structured(system="s", messages=[], output_model=WeekPlan)[0].summary


def test_an_invalid_answer_gets_one_repair_with_the_error_fed_back(make):
    provider, client = make(reply('{"summary": 5}'), reply(json.dumps(PLAN)))
    plan, used = provider.structured(system="s", messages=[{"role": "user", "content": "plan"}], output_model=WeekPlan)
    assert plan.summary == "A good week." and used["output_tokens"] == 14
    repair = client.calls[1]["messages"]
    assert repair[-2] == {"role": "assistant", "content": '{"summary": 5}'}
    assert "not valid" in repair[-1]["content"] and "corrected JSON" in repair[-1]["content"]


def test_two_invalid_answers_raise_after_exactly_two_calls(make):
    provider, client = make(reply("not json at all"), reply("still not json"))
    with pytest.raises(StructuredOutputError):
        provider.structured(system="s", messages=[], output_model=WeekPlan)
    assert len(client.calls) == 2


def test_a_rejected_json_object_mode_is_a_clear_error(make):
    provider, _ = make(
        http_error(openai.BadRequestError, 400, "no schema"), http_error(openai.BadRequestError, 400, "no json mode either")
    )
    with pytest.raises(LLMError, match="no json mode either"):
        provider.structured(system="s", messages=[], output_model=WeekPlan)


def test_rate_limits_during_structured_output_are_mapped(make):
    provider, _ = make(http_error(openai.RateLimitError, 429))
    with pytest.raises(LLMError, match="rate limiting"):
        provider.structured(system="s", messages=[], output_model=WeekPlan)


def test_parse_json_text_rejects_text_without_an_object():
    with pytest.raises(ValueError):
        parse_json_text("no braces here")
    assert parse_json_text(' {"a": 1} ') == {"a": 1}
