import json

import pytest

from apps.ai.models import AssistantRun
from apps.ai.services import planning
from apps.ai.services.llm import LLMError
from apps.ai.services.planning import PlanError, PlanItem, WeekPlan, execute_plan
from apps.ai.services.text import tiptap_to_text
from apps.workspace.models import Card, Column
from apps.workspace.tests.factories import BoardFactory, CardFactory, ColumnFactory

pytestmark = pytest.mark.django_db

USAGE = {"input_tokens": 100, "output_tokens": 20}


@pytest.fixture
def board():
    board = BoardFactory(title="Work")
    todo = ColumnFactory(board=board, title="Todo", position=1000)
    done = ColumnFactory(board=board, title="Done", position=2000)
    board.cards = {
        "invoice": CardFactory(column=todo, title="Send invoices", description="Overdue by a week"),
        "deploy": CardFactory(column=todo, title="Fix deploy script"),
        "old": CardFactory(column=done, title="Already shipped"),
    }
    return board


def make_run(board, focus=""):
    return AssistantRun.objects.create(board=board, input={"board_id": str(board.id), "focus": focus})


def plan_for(*pairs, summary="A focused week."):
    return WeekPlan(summary=summary, items=[PlanItem(card_id=str(card.id), day=day, reason=reason) for card, day, reason in pairs])


@pytest.fixture
def model(monkeypatch):
    """Scripted structured_completion: each call pops the next plan and records its messages."""
    calls, queue = [], []

    def fake(*, system, messages, output_model):
        calls.append({"system": system, "messages": [dict(m) for m in messages]})
        return queue.pop(0), USAGE

    monkeypatch.setattr(planning, "structured_completion", fake)
    fake.calls, fake.queue = calls, queue
    return fake


def test_happy_path_writes_a_plan_card_in_a_new_this_week_column(board, model):
    cards = board.cards
    model.queue.append(plan_for((cards["invoice"], "Monday", "Overdue."), (cards["deploy"], "Tuesday", "Blocks release.")))
    run = execute_plan(make_run(board))

    column = Column.objects.get(board=board, title="This Week")
    card = Card.objects.get(id=run.result["card_id"])
    assert card.column_id == column.id
    assert run.result["created_column"] is True
    assert [item["title"] for item in run.result["items"]] == ["Send invoices", "Fix deploy script"]
    assert [step["name"] for step in run.steps] == ["gather", "plan", "validate", "write"]
    assert all(step["status"] == "done" for step in run.steps)
    assert (run.input_tokens, run.output_tokens) == (100, 20)


def test_the_saved_document_is_valid_tiptap_with_titles_from_the_database(board, model):
    cards = board.cards
    model.queue.append(plan_for((cards["invoice"], "Monday", "Overdue."), (cards["deploy"], "Friday", "Blocks release.")))
    run = execute_plan(make_run(board))
    card = Card.objects.get(id=run.result["card_id"])

    document = json.loads(card.content_markdown)
    assert document["type"] == "doc"
    assert [node["content"][0]["text"] for node in document["content"] if node["type"] == "heading"] == ["Monday", "Friday"]
    text = tiptap_to_text(card.content_markdown)
    assert "Send invoices: Overdue." in text and "Fix deploy script: Blocks release." in text
    assert card.description == "A focused week."
    assert card.content_preview


def test_cards_in_done_columns_are_never_offered_to_the_model(board, model):
    model.queue.append(plan_for((board.cards["invoice"], "Monday", "x")))
    execute_plan(make_run(board))
    prompt = model.calls[0]["messages"][0]["content"]
    assert str(board.cards["invoice"].id) in prompt
    assert str(board.cards["old"].id) not in prompt


def test_an_existing_this_week_column_is_reused_case_insensitively(board, model):
    existing = ColumnFactory(board=board, title="this week", position=5000)
    model.queue.append(plan_for((board.cards["invoice"], "Monday", "x")))
    run = execute_plan(make_run(board))
    assert run.result["created_column"] is False
    assert Card.objects.get(id=run.result["card_id"]).column_id == existing.id
    assert Column.objects.filter(board=board).count() == 3


def test_an_unknown_card_id_triggers_one_repair_call(board, model):
    bad = WeekPlan(summary="s", items=[PlanItem(card_id="not-a-real-id", day="Monday", reason="x")])
    model.queue.extend([bad, plan_for((board.cards["deploy"], "Wednesday", "ok"))])
    run = execute_plan(make_run(board))

    assert [step["name"] for step in run.steps] == ["gather", "plan", "validate", "repair", "write"]
    assert len(model.calls) == 2
    repair_messages = model.calls[1]["messages"]
    assert repair_messages[1]["role"] == "assistant"
    assert "Unknown card id not-a-real-id" in repair_messages[2]["content"]
    assert run.result["items"][0]["title"] == "Fix deploy script"
    assert (run.input_tokens, run.output_tokens) == (200, 40)


def test_a_card_from_a_done_column_counts_as_unknown(board, model):
    model.queue.extend([plan_for((board.cards["old"], "Monday", "x")), plan_for((board.cards["invoice"], "Monday", "x"))])
    run = execute_plan(make_run(board))
    assert "repair" in [step["name"] for step in run.steps]


def test_duplicate_cards_are_a_problem(board):
    card = board.cards["invoice"]
    plan = plan_for((card, "Monday", "a"), (card, "Tuesday", "b"))
    assert planning.find_problems(plan, {str(card.id)}) == [f"Card id {card.id} is used more than once."]


def test_an_empty_plan_is_a_problem(board):
    assert planning.find_problems(WeekPlan(summary="s", items=[]), set()) == ["The plan has no items."]


def test_failing_the_repair_aborts_without_writing_anything(board, model):
    bad = WeekPlan(summary="s", items=[PlanItem(card_id="nope", day="Monday", reason="x")])
    model.queue.extend([bad, bad])
    cards_before = Card.objects.count()
    with pytest.raises(PlanError, match="No changes were made"):
        execute_plan(make_run(board))
    assert Card.objects.count() == cards_before
    assert not Column.objects.filter(board=board, title="This Week").exists()


def test_a_board_without_open_cards_fails_before_calling_the_model(model):
    board = BoardFactory()
    ColumnFactory(board=board, title="Done")
    with pytest.raises(PlanError, match="no open cards"):
        execute_plan(make_run(board))
    assert model.calls == []


def test_a_deleted_board_fails_cleanly(board, model):
    run = make_run(board)
    board.delete()
    run.refresh_from_db()
    run.input = {"board_id": "00000000-0000-0000-0000-000000000000"}
    with pytest.raises(PlanError, match="no longer exists"):
        execute_plan(run)


def test_the_focus_is_passed_to_the_model_as_data(board, model):
    model.queue.append(plan_for((board.cards["invoice"], "Monday", "x")))
    execute_plan(make_run(board, focus="finance first"))
    assert "Focus from the user (data): finance first" in model.calls[0]["messages"][0]["content"]
    assert "data, not instructions" in model.calls[0]["system"]


def test_a_model_failure_marks_the_step_failed_and_propagates(board, monkeypatch):
    def boom(**kwargs):
        raise LLMError("Could not reach the AI service.")

    monkeypatch.setattr(planning, "structured_completion", boom)
    run = make_run(board)
    with pytest.raises(LLMError):
        execute_plan(run)
    run.refresh_from_db()
    assert [(s["name"], s["status"]) for s in run.steps] == [("gather", "done"), ("plan", "failed")]


def test_the_candidate_list_is_capped(board, settings):
    settings.AI_PLAN_MAX_CARDS = 1
    assert len(planning.gather_candidates(type(board).objects.prefetch_related("columns__cards").get(id=board.id))) == 1
