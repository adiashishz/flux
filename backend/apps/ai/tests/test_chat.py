import json

import pytest

from apps.ai.services import chat
from apps.workspace.models import Card
from apps.workspace.tests.factories import CardFactory, ColumnFactory

from apps.ai.services.providers.base import LLMError

from .fakes import FakeProvider, final_message, text_block, tool_use_block

pytestmark = pytest.mark.django_db


@pytest.fixture
def script(monkeypatch):
    def install(*finals):
        provider = FakeProvider(*finals)
        monkeypatch.setattr(chat, "get_provider", lambda: provider)
        return provider

    return install


def run(messages=None, board_id=None):
    return list(chat.run_chat(messages or [{"role": "user", "content": "hi"}], board_id=board_id))


def kinds(events):
    return [event["type"] for event in events]


def test_plain_answer_streams_text_then_done(script):
    script(final_message(text_block("Hello there")))
    events = run()
    assert kinds(events) == ["text", "done"]
    assert events[0]["text"] == "Hello there"
    assert events[-1]["usage"] == {"input_tokens": 10, "output_tokens": 5}


def test_tool_call_runs_and_the_result_goes_back_to_the_model(script):
    column = ColumnFactory()
    client = script(
        final_message(text_block("On it."), tool_use_block("t1", "create_card", {"column_id": str(column.id), "title": "Ship"})),
        final_message(text_block("Created Ship.")),
    )
    events = run()

    assert kinds(events) == ["text", "tool_call", "tool_result", "text", "done"]
    assert Card.objects.filter(title="Ship", column=column).exists()

    second_request = client.calls[1]["messages"]
    assert second_request[1]["role"] == "assistant"
    assert second_request[1]["content"][1] == {
        "type": "tool_use", "id": "t1", "name": "create_card",
        "input": {"column_id": str(column.id), "title": "Ship"},
    }
    result_block = second_request[2]["content"][0]
    assert result_block["tool_use_id"] == "t1" and result_block["is_error"] is False
    assert json.loads(result_block["content"])["title"] == "Ship"


def test_a_failing_tool_becomes_an_error_result_not_a_crash(script):
    client = script(
        final_message(tool_use_block("t1", "get_board", {"board_id": "garbage"})),
        final_message(text_block("That id looks wrong.")),
    )
    events = run()
    assert [e["ok"] for e in events if e["type"] == "tool_result"] == [False]
    assert client.calls[1]["messages"][-1]["content"][0]["is_error"] is True
    assert kinds(events)[-1] == "done"


def test_delete_asks_for_confirmation_and_deletes_nothing(script):
    card = CardFactory(title="Keep")
    script(
        final_message(tool_use_block("t1", "delete_card", {"card_id": str(card.id)})),
        final_message(text_block("Please confirm the deletion.")),
    )
    events = run()
    confirmation = next(e for e in events if e["type"] == "confirmation_required")
    assert confirmation["card_id"] == str(card.id) and confirmation["title"] == "Keep"
    assert Card.objects.filter(id=card.id).exists()


def test_several_tool_calls_in_one_turn_all_get_results(script):
    column = ColumnFactory()
    client = script(
        final_message(
            tool_use_block("a", "create_card", {"column_id": str(column.id), "title": "One"}),
            tool_use_block("b", "create_card", {"column_id": str(column.id), "title": "Two"}),
        ),
        final_message(text_block("Done.")),
    )
    run()
    results = client.calls[1]["messages"][-1]["content"]
    assert [r["tool_use_id"] for r in results] == ["a", "b"]
    assert Card.objects.filter(column=column).count() == 2


def test_the_loop_stops_at_the_iteration_cap(script, settings):
    settings.AI_MAX_ITERATIONS = 3
    column = ColumnFactory()
    looping = [
        final_message(tool_use_block(f"t{n}", "create_card", {"column_id": str(column.id), "title": f"c{n}"}))
        for n in range(10)
    ]
    client = script(*looping)
    events = run()
    assert len(client.calls) == 3
    assert events[-1]["type"] == "error" and "Stopped after 3 steps" in events[-1]["message"]
    assert Card.objects.count() == 3


def test_model_failures_become_a_clean_error_event(script):
    script(LLMError("Could not reach the AI service."))
    events = run()
    assert kinds(events) == ["error"]
    assert events[0]["message"] == "Could not reach the AI service."


def test_a_misconfigured_provider_is_an_error_event_not_a_crash(monkeypatch):
    def broken():
        raise LLMError("Set AI_MODEL to a model your 'gemini' account can use.")

    monkeypatch.setattr(chat, "get_provider", broken)
    events = run()
    assert kinds(events) == ["error"] and "AI_MODEL" in events[0]["message"]


def test_arguments_the_provider_could_not_parse_go_back_to_the_model_as_an_error(script):
    from apps.ai.services.providers.base import ToolCall, TurnResult

    broken = TurnResult(tool_calls=[ToolCall("t1", "create_card", {}, error="Arguments were not valid JSON.")], stop_reason="tool_use")
    client = script(broken, final_message(text_block("Sorry, retrying.")))
    events = run()
    assert [e["ok"] for e in events if e["type"] == "tool_result"] == [False]
    result = client.calls[1]["messages"][-1]["content"][0]
    assert result["is_error"] is True and "not valid JSON" in result["content"]


def test_the_system_prompt_mentions_the_current_board(script):
    column = ColumnFactory(board__title="Roadmap")
    client = script(final_message(text_block("ok")))
    run(board_id=column.board_id)
    assert "Roadmap" in client.calls[0]["system"]
    assert str(column.board_id) in client.calls[0]["system"]


def test_requests_offer_the_tools(script):
    client = script(final_message(text_block("ok")))
    run()
    assert {tool["name"] for tool in client.calls[0]["tools"]} >= {"create_card", "move_card", "delete_card"}
