from types import SimpleNamespace

import anthropic
import httpx
import pytest

from apps.ai.services.providers.anthropic_provider import AnthropicProvider
from apps.ai.services.providers.base import LLMError, StructuredOutputError
from apps.ai.services.providers.base import assistant_blocks
from apps.ai.services.providers.base import ToolCall, TurnResult
from apps.ai.services.planning import WeekPlan

from .fakes import FakeClient, final_message, text_block, tool_use_block

REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


@pytest.fixture
def provider(monkeypatch):
    provider = AnthropicProvider("key", "model-x")

    def install(*finals):
        client = FakeClient(*finals)
        monkeypatch.setattr(provider, "_client", lambda: client)
        return client

    provider.install = install
    return provider


def drain(provider):
    pieces = list(provider.stream_turn(system="s", messages=[{"role": "user", "content": "hi"}], tools=[]))
    return [p for kind, p in pieces if kind == "text"], [p for kind, p in pieces if kind == "turn"][0]


def test_text_events_stream_and_the_turn_comes_last(provider):
    provider.install(final_message(text_block("Hello")))
    texts, turn = drain(provider)
    assert texts == ["Hello"] and turn.text == "Hello"
    assert (turn.stop_reason, turn.tool_calls, turn.usage) == ("end_turn", [], {"input_tokens": 10, "output_tokens": 5})


def test_tool_use_blocks_become_tool_calls(provider):
    provider.install(final_message(text_block("On it."), tool_use_block("t1", "create_card", {"title": "A"})))
    _, turn = drain(provider)
    assert turn.stop_reason == "tool_use"
    assert turn.tool_calls == [ToolCall("t1", "create_card", {"title": "A"})]


def test_the_request_uses_the_configured_model_system_and_tools(provider, settings):
    settings.AI_MAX_TOKENS = 77
    client = provider.install(final_message(text_block("ok")))
    list(provider.stream_turn(system="sys", messages=[{"role": "user", "content": "hi"}], tools=[{"name": "t"}]))
    call = client.calls[0]
    assert (call["model"], call["system"], call["max_tokens"], call["tools"]) == ("model-x", "sys", 77, [{"name": "t"}])


@pytest.mark.parametrize("raw,expected", [("max_tokens", "max_tokens"), ("refusal", "refusal"), ("stop_sequence", "end_turn"), (None, "end_turn")])
def test_stop_reasons_are_normalised(provider, raw, expected):
    provider.install(final_message(text_block("x"), stop_reason=raw))
    assert drain(provider)[1].stop_reason == expected


@pytest.mark.parametrize(
    "error,message",
    [
        (anthropic.APIConnectionError(request=REQUEST), "Could not reach the AI service."),
        (anthropic.AuthenticationError("no", response=httpx.Response(401, request=REQUEST), body=None), "The AI service rejected the API key."),
        (anthropic.RateLimitError("slow", response=httpx.Response(429, request=REQUEST), body=None), "rate limiting"),
        (anthropic.InternalServerError("boom", response=httpx.Response(500, request=REQUEST), body=None), "returned an error"),
    ],
)
def test_sdk_errors_become_llm_errors_with_safe_messages(provider, monkeypatch, error, message):
    class Failing:
        def __init__(self):
            self.messages = self

        def stream(self, **kwargs):
            raise error

    monkeypatch.setattr(provider, "_client", lambda: Failing())
    with pytest.raises(LLMError, match=message):
        drain(provider)


def test_structured_returns_the_parsed_model_and_usage(provider, monkeypatch):
    plan = WeekPlan(summary="s", items=[])
    parsed = SimpleNamespace(parsed_output=plan, stop_reason="end_turn", usage=SimpleNamespace(input_tokens=3, output_tokens=4))
    client = SimpleNamespace(messages=SimpleNamespace(parse=lambda **kwargs: parsed))
    monkeypatch.setattr(provider, "_client", lambda: client)
    assert provider.structured(system="s", messages=[], output_model=WeekPlan) == (plan, {"input_tokens": 3, "output_tokens": 4})


def test_structured_without_a_parsed_answer_is_a_structured_output_error(provider, monkeypatch):
    empty = SimpleNamespace(parsed_output=None, stop_reason="max_tokens", usage=SimpleNamespace(input_tokens=1, output_tokens=1))
    monkeypatch.setattr(provider, "_client", lambda: SimpleNamespace(messages=SimpleNamespace(parse=lambda **kwargs: empty)))
    with pytest.raises(StructuredOutputError, match="max_tokens"):
        provider.structured(system="s", messages=[], output_model=WeekPlan)


def test_assistant_blocks_put_text_before_tool_calls():
    turn = TurnResult(text="Plan", tool_calls=[ToolCall("a", "get_board", {"board_id": "b"})])
    assert assistant_blocks(turn) == [
        {"type": "text", "text": "Plan"},
        {"type": "tool_use", "id": "a", "name": "get_board", "input": {"board_id": "b"}},
    ]
    assert assistant_blocks(TurnResult()) == []
