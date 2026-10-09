import json

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.ai.services import chat

from .fakes import FakeClient, final_message, text_block

pytestmark = pytest.mark.django_db

URL = "/api/v1/ai/chat/"
BODY = {"messages": [{"role": "user", "content": "hello"}]}


@pytest.fixture(autouse=True)
def enabled(settings, monkeypatch):
    settings.AI_ENABLED = True
    settings.ANTHROPIC_API_KEY = "test-key"
    cache.clear()
    monkeypatch.setattr(chat, "get_client", lambda: FakeClient(final_message(text_block("Hi!"))))


def parse_sse(response):
    body = b"".join(response.streaming_content).decode()
    events = []
    for chunk in filter(None, body.split("\n\n")):
        event_line, data_line = chunk.split("\n")
        events.append((event_line.removeprefix("event: "), json.loads(data_line.removeprefix("data: "))))
    return events


def test_streams_server_sent_events():
    response = APIClient().post(URL, BODY, format="json")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/event-stream"
    assert response["X-Accel-Buffering"] == "no"
    assert response["Cache-Control"] == "no-cache"
    events = parse_sse(response)
    assert [name for name, _ in events] == ["text", "done"]
    assert events[0][1]["text"] == "Hi!"


@pytest.mark.parametrize("flag,key", [(False, "k"), (True, "")])
def test_disabled_or_unkeyed_returns_503(settings, flag, key):
    settings.AI_ENABLED = flag
    settings.ANTHROPIC_API_KEY = key
    assert APIClient().post(URL, BODY, format="json").status_code == 503


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"messages": []},
        {"messages": [{"role": "system", "content": "x"}]},
        {"messages": [{"role": "user", "content": ""}]},
        {"messages": [{"role": "user", "content": "x" * 4001}]},
        {"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]},
        {"messages": [{"role": "user", "content": "hi"}] * 21},
        {"messages": [{"role": "user", "content": "hi"}], "board_id": "nope"},
    ],
)
def test_invalid_requests_are_rejected(body):
    assert APIClient().post(URL, body, format="json").status_code == 400


def test_the_rate_limit_returns_429(monkeypatch):
    from rest_framework.throttling import ScopedRateThrottle

    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"ai": "2/min"})
    client = APIClient()
    statuses = []
    for _ in range(3):
        response = client.post(URL, BODY, format="json")
        if response.status_code == 200:
            b"".join(response.streaming_content)
        statuses.append(response.status_code)
    assert statuses == [200, 200, 429]
