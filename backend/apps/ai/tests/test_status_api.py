import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean(settings):
    settings.AI_ENABLED = True
    settings.AI_PROVIDER = "gemini"
    settings.AI_MODEL = "gem-model"
    settings.AI_API_KEY = "super-secret-key"
    settings.AI_BASE_URL = ""
    settings.AI_PROVIDER_KEYS = {}


def status():
    return APIClient().get("/api/v1/ai/status/")


def test_a_configured_provider_is_reported_ready():
    body = status().json()
    assert body == {"enabled": True, "configured": True, "provider": "gemini", "model": "gem-model", "problem": None}


def test_the_status_never_contains_a_key():
    assert "super-secret-key" not in status().content.decode()


def test_a_missing_model_is_explained(settings):
    settings.AI_MODEL = ""
    body = status().json()
    assert body["configured"] is False and "AI_MODEL" in body["problem"]


def test_disabled_is_reported_separately_from_configured(settings):
    settings.AI_ENABLED = False
    body = status().json()
    assert body["enabled"] is False and body["configured"] is True


def test_the_chat_and_plan_endpoints_follow_the_same_gate(settings):
    settings.AI_MODEL = ""
    client = APIClient()
    assert client.post("/api/v1/ai/chat/", {"messages": [{"role": "user", "content": "hi"}]}, format="json").status_code == 503
    assert client.post("/api/v1/ai/plans/", {"board_id": "6c2e97c5-2ea0-4066-9e9a-e4320c6dc6a7"}, format="json").status_code == 503
