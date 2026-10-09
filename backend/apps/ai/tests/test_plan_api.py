import uuid
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ai.api.v1 import plans
from apps.ai.models import AssistantRun
from apps.workspace.tests.factories import BoardFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enabled(settings):
    settings.AI_ENABLED = True
    settings.ANTHROPIC_API_KEY = "test-key"
    cache.clear()


@pytest.fixture
def enqueued(monkeypatch):
    calls = []
    monkeypatch.setattr(plans.run_plan_week, "delay", lambda run_id: calls.append(run_id))
    return calls


def post(body):
    return APIClient().post("/api/v1/ai/plans/", body, format="json")


def test_starting_a_plan_returns_202_and_enqueues_the_run(enqueued):
    board = BoardFactory()
    response = post({"board_id": str(board.id), "focus": " ship the release "})
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued" and enqueued == [body["id"]]
    run = AssistantRun.objects.get(id=body["id"])
    assert run.input == {"board_id": str(board.id), "focus": "ship the release"} and run.board_id == board.id


def test_unknown_board_is_404(enqueued):
    assert post({"board_id": str(uuid.uuid4())}).status_code == 404
    assert enqueued == []


@pytest.mark.parametrize("body", [{}, {"board_id": "nope"}, {"board_id": str(uuid.uuid4()), "focus": "x" * 301}])
def test_invalid_requests_are_400(body, enqueued):
    assert post(body).status_code == 400


@pytest.mark.parametrize("flag,key", [(False, "k"), (True, "")])
def test_disabled_or_unkeyed_is_503(settings, enqueued, flag, key):
    settings.AI_ENABLED, settings.ANTHROPIC_API_KEY = flag, key
    assert post({"board_id": str(BoardFactory().id)}).status_code == 503


def test_a_down_queue_fails_the_run_instead_of_leaving_it_queued(monkeypatch):
    def broker_down(run_id):
        raise ConnectionError("redis is down")

    monkeypatch.setattr(plans.run_plan_week, "delay", broker_down)
    response = post({"board_id": str(BoardFactory().id)})
    assert response.status_code == 503
    run = AssistantRun.objects.get()
    assert (run.status, run.error_message) == ("failed", "The background queue is not available.")


def test_run_detail_reports_status_steps_and_result():
    run = AssistantRun.objects.create(
        status="succeeded", steps=[{"name": "gather", "status": "done"}], result={"card_id": "c1"}, input_tokens=7
    )
    body = APIClient().get(f"/api/v1/ai/runs/{run.id}/").json()
    assert body["status"] == "succeeded" and body["result"] == {"card_id": "c1"}
    assert body["steps"][0]["name"] == "gather" and body["input_tokens"] == 7


def test_unknown_run_is_404():
    assert APIClient().get(f"/api/v1/ai/runs/{uuid.uuid4()}/").status_code == 404


def test_a_stuck_run_is_marked_failed_when_polled(settings):
    settings.AI_RUN_STALE_SECONDS = 60
    run = AssistantRun.objects.create(status="running")
    AssistantRun.objects.filter(id=run.id).update(updated_at=timezone.now() - timedelta(seconds=120))
    body = APIClient().get(f"/api/v1/ai/runs/{run.id}/").json()
    assert (body["status"], body["error_message"]) == ("failed", "The run timed out.")


def test_a_fresh_run_is_left_alone(settings):
    settings.AI_RUN_STALE_SECONDS = 60
    run = AssistantRun.objects.create(status="running")
    assert APIClient().get(f"/api/v1/ai/runs/{run.id}/").json()["status"] == "running"


def test_a_finished_run_is_never_touched_by_the_stale_check(settings):
    settings.AI_RUN_STALE_SECONDS = 1
    run = AssistantRun.objects.create(status="succeeded")
    AssistantRun.objects.filter(id=run.id).update(updated_at=timezone.now() - timedelta(hours=1))
    assert APIClient().get(f"/api/v1/ai/runs/{run.id}/").json()["status"] == "succeeded"
