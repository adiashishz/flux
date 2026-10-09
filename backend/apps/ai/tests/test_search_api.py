import pytest
from rest_framework.test import APIClient

from apps.ai.models import CardEmbedding
from apps.ai.services import embeddings
from apps.workspace.tests.factories import CardFactory

pytestmark = pytest.mark.django_db


def unit(*weights):
    vector = [0.0] * 384
    for index, weight in enumerate(weights):
        vector[index] = weight
    return vector


def store(card, vector):
    CardEmbedding.objects.create(card=card, embedding=vector, text_hash="h", model_name="m")


@pytest.fixture
def query_vector(monkeypatch):
    monkeypatch.setattr(embeddings, "embed_query", lambda text: unit(1.0, 0.0))


def test_results_are_ordered_by_similarity(query_vector):
    closest = CardFactory(title="Closest")
    nearby = CardFactory(title="Nearby")
    store(nearby, unit(1.0, 1.0))
    store(closest, unit(1.0, 0.0))

    results = APIClient().get("/api/v1/ai/search/", {"q": "anything"}).json()

    assert [r["title"] for r in results] == ["Closest", "Nearby"]
    assert results[0]["score"] == 1.0
    assert 0.7 < results[1]["score"] < 0.72


def test_cards_below_the_score_cutoff_are_dropped(query_vector):
    unrelated = CardFactory(title="Unrelated")
    store(unrelated, unit(0.0, 1.0))
    assert APIClient().get("/api/v1/ai/search/", {"q": "anything"}).json() == []


def test_results_include_location_for_navigation(query_vector):
    card = CardFactory(title="Located")
    store(card, unit(1.0, 0.0))
    result = APIClient().get("/api/v1/ai/search/", {"q": "x"}).json()[0]
    assert result["column_id"] == str(card.column_id)
    assert result["board_id"] == str(card.column.board_id)
    assert result["board_title"] == card.column.board.title


def test_the_result_limit_is_applied(query_vector, settings):
    settings.AI_SEARCH_LIMIT = 2
    for number in range(4):
        store(CardFactory(title=f"Card {number}"), unit(1.0, 0.0))
    assert len(APIClient().get("/api/v1/ai/search/", {"q": "x"}).json()) == 2


def test_an_empty_query_returns_nothing_without_embedding(monkeypatch):
    def boom(text):
        raise AssertionError("embed_query must not run for an empty query")

    monkeypatch.setattr(embeddings, "embed_query", boom)
    assert APIClient().get("/api/v1/ai/search/", {"q": "  "}).json() == []
