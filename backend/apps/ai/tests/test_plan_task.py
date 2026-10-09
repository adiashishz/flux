import pytest

from apps.ai import tasks
from apps.ai.models import AssistantRun
from apps.ai.services.llm import LLMError
from apps.ai.services.planning import PlanError
from apps.workspace.tests.factories import BoardFactory

pytestmark = pytest.mark.django_db


def queued_run():
    board = BoardFactory()
    return AssistantRun.objects.create(board=board, input={"board_id": str(board.id)})


def test_success_saves_the_result_and_marks_the_run_succeeded(monkeypatch):
    run = queued_run()

    def fake_execute(r):
        r.result = {"card_id": "c1"}
        r.input_tokens = 5
        return r

    monkeypatch.setattr(tasks, "execute_plan", fake_execute)
    assert tasks.run_plan_week(str(run.id)) == "succeeded"
    run.refresh_from_db()
    assert (run.status, run.result, run.input_tokens) == ("succeeded", {"card_id": "c1"}, 5)


@pytest.mark.parametrize("error", [PlanError("No open cards."), LLMError("Could not reach the AI service.")])
def test_known_failures_show_their_message(monkeypatch, error):
    run = queued_run()

    def boom(r):
        raise error

    monkeypatch.setattr(tasks, "execute_plan", boom)
    assert tasks.run_plan_week(str(run.id)) == "failed"
    run.refresh_from_db()
    assert (run.status, run.error_message) == ("failed", str(error))


def test_unexpected_errors_are_hidden_from_the_user(monkeypatch):
    run = queued_run()

    def boom(r):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(tasks, "execute_plan", boom)
    assert tasks.run_plan_week(str(run.id)) == "crashed"
    run.refresh_from_db()
    assert run.error_message == "Planning failed unexpectedly."
    assert "secret" not in run.error_message


def test_a_run_that_is_not_queued_is_skipped(monkeypatch):
    run = queued_run()
    AssistantRun.objects.filter(id=run.id).update(status=AssistantRun.RUNNING)
    monkeypatch.setattr(tasks, "execute_plan", lambda r: pytest.fail("must not run twice"))
    assert tasks.run_plan_week(str(run.id)) == "skipped"


def test_a_run_that_timed_out_meanwhile_is_not_overwritten(monkeypatch):
    run = queued_run()

    def slow(r):
        AssistantRun.objects.filter(id=r.id).update(status=AssistantRun.FAILED, error_message="The run timed out.")
        r.result = {"late": True}
        return r

    monkeypatch.setattr(tasks, "execute_plan", slow)
    tasks.run_plan_week(str(run.id))
    run.refresh_from_db()
    assert (run.status, run.error_message, run.result) == ("failed", "The run timed out.", None)


def test_an_unknown_run_is_ignored():
    assert tasks.run_plan_week("00000000-0000-0000-0000-000000000000") == "skipped"
