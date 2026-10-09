import pytest

from apps.ai.evals.tools import run_case, run_tools
from apps.ai.evals.world import build_world, load_dataset
from apps.ai.services import chat
from apps.workspace.models import Card

from apps.ai.services.providers.base import LLMError

from .fakes import FakeProvider, final_message, text_block, tool_use_block

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    return build_world(load_dataset("corpus"), embed=False)


@pytest.fixture
def play(monkeypatch):
    def install(*finals):
        provider = FakeProvider(*finals)
        monkeypatch.setattr(chat, "get_provider", lambda: provider)
        return provider

    return install


def case(case_id):
    return next(c for c in load_dataset("tools")["cases"] if c["id"] == case_id)


def test_a_correct_create_passes_and_is_rolled_back(world, play):
    cards_before = Card.objects.count()
    play(
        final_message(tool_use_block("t1", "create_card", {"column_id": str(world.columns["work_todo"].id), "title": "Prepare demo for Friday"})),
        final_message(text_block("Done.")),
    )
    result = run_case(world, case("create-basic"))
    assert result["passed"] and result["tool_calls"] == ["create_card"] and result["iterations"] == 2
    assert Card.objects.count() == cards_before


def test_creating_in_the_wrong_column_fails(world, play):
    play(
        final_message(tool_use_block("t1", "create_card", {"column_id": str(world.columns["home_todo"].id), "title": "Prepare demo for Friday"})),
        final_message(text_block("Done.")),
    )
    result = run_case(world, case("create-basic"))
    assert not result["passed"] and "no new card in work_todo" in result["failures"][0]


def test_answering_without_acting_fails_a_task(world, play):
    play(final_message(text_block("Sure, I can do that.")))
    assert not run_case(world, case("move-by-title"))["passed"]


def test_a_correct_move_passes(world, play):
    card = world.cards["w02"]
    play(
        final_message(tool_use_block("t1", "move_card", {"card_id": str(card.id), "destination_column_id": str(world.columns["work_doing"].id), "destination_index": 0})),
        final_message(text_block("Moved.")),
    )
    assert run_case(world, case("move-by-title"))["passed"]


def test_move_to_top_checks_the_index(world, play):
    card, doing = world.cards["w04"], world.columns["work_doing"]
    play(
        final_message(tool_use_block("t1", "move_card", {"card_id": str(card.id), "destination_column_id": str(doing.id), "destination_index": 5})),
        final_message(text_block("Moved.")),
    )
    assert not run_case(world, case("move-to-top"))["passed"]
    play(
        final_message(tool_use_block("t1", "move_card", {"card_id": str(card.id), "destination_column_id": str(doing.id), "destination_index": 0})),
        final_message(text_block("Moved.")),
    )
    assert run_case(world, case("move-to-top"))["passed"]


def test_delete_must_ask_and_must_not_delete(world, play):
    play(
        final_message(tool_use_block("t1", "delete_card", {"card_id": str(world.cards["h06"].id)})),
        final_message(text_block("Please confirm.")),
    )
    assert run_case(world, case("delete-asks-first"))["passed"]


def test_a_read_only_question_must_not_change_anything(world, play):
    play(
        final_message(tool_use_block("t1", "get_board", {"board_id": str(world.boards["work"].id)})),
        final_message(text_block("Here is the board.")),
    )
    assert run_case(world, case("read-only"))["passed"]
    play(
        final_message(tool_use_block("t1", "get_board", {"board_id": str(world.boards["work"].id)}), tool_use_block("t2", "create_card", {"column_id": str(world.columns["work_todo"].id), "title": "Oops"})),
        final_message(text_block("Here is the board.")),
    )
    result = run_case(world, case("read-only"))
    assert not result["passed"] and "no_mutation" in result["failures"][0]


def test_asking_a_clarifying_question_passes_the_ambiguous_case(world, play):
    play(final_message(text_block("Which card do you mean?")))
    assert run_case(world, case("ambiguous-asks"))["passed"]


def test_creating_two_cards_needs_both(world, play):
    column = str(world.columns["home_todo"].id)
    play(
        final_message(tool_use_block("a", "create_card", {"column_id": column, "title": "Buy gift"})),
        final_message(text_block("Created one.")),
    )
    assert not run_case(world, case("create-two"))["passed"]
    play(
        final_message(tool_use_block("a", "create_card", {"column_id": column, "title": "Buy gift"}), tool_use_block("b", "create_card", {"column_id": column, "title": "Wrap gift"})),
        final_message(text_block("Created both.")),
    )
    assert run_case(world, case("create-two"))["passed"]


def test_a_model_error_fails_the_case(world, play):
    play(LLMError("Could not reach the AI service."))
    result = run_case(world, case("create-basic"))
    assert not result["passed"] and "model error" in result["failures"][-1]


def test_the_summary_counts_passes(world, play):
    dataset = {"cases": [case("ambiguous-asks"), case("move-by-title")]}
    play(final_message(text_block("Which card?")), final_message(text_block("Sure.")))
    summary = run_tools(world, dataset)
    assert (summary["cases"], summary["passed"], summary["accuracy"]) == (2, 1, 0.5)
