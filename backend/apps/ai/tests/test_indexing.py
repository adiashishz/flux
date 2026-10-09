import hashlib

import pytest

from apps.ai.models import CardEmbedding
from apps.ai.services import embeddings, indexing
from apps.workspace.services.card_service import CardService
from apps.workspace.tests.factories import CardFactory, ColumnFactory

pytestmark = pytest.mark.django_db


def one_hot(index):
    vector = [0.0] * 384
    vector[index] = 1.0
    return vector


@pytest.fixture
def fake_embedder(monkeypatch):
    calls = []

    def embed_passages(texts):
        calls.append(list(texts))
        return [one_hot(int(hashlib.sha256(text.encode()).hexdigest(), 16) % 384) for text in texts]

    monkeypatch.setattr(embeddings, "embed_passages", embed_passages)
    return calls


def test_a_new_card_is_embedded(fake_embedder):
    card = CardFactory(title="Quarterly report")
    assert indexing.index_card(card.id) == indexing.EMBEDDED
    stored = CardEmbedding.objects.get(card=card)
    assert len(stored.embedding) == 384
    assert stored.model_name == "BAAI/bge-small-en-v1.5"


def test_unchanged_text_is_not_embedded_again(fake_embedder):
    card = CardFactory(title="Stable")
    indexing.index_card(card.id)
    assert indexing.index_card(card.id) == indexing.UNCHANGED
    assert len(fake_embedder) == 1


def test_changed_text_is_embedded_again(fake_embedder):
    card = CardFactory(title="Before")
    indexing.index_card(card.id)
    CardService.update_card(card.id, title="After")
    assert indexing.index_card(card.id) == indexing.EMBEDDED
    assert len(fake_embedder) == 2


def test_a_model_change_forces_a_re_embed(fake_embedder, settings):
    card = CardFactory(title="Same text")
    indexing.index_card(card.id)
    settings.EMBEDDING_MODEL = "another/model"
    assert indexing.index_card(card.id) == indexing.EMBEDDED


def test_a_deleted_card_is_reported_missing(fake_embedder):
    card = CardFactory()
    card_id = card.id
    card.delete()
    assert indexing.index_card(card_id) == indexing.MISSING


def test_deleting_a_card_removes_its_embedding(fake_embedder):
    card = CardFactory()
    indexing.index_card(card.id)
    CardService.delete_card(card.id)
    assert CardEmbedding.objects.count() == 0


class TestEnqueueOnSave:
    @pytest.fixture
    def delay(self, monkeypatch, settings):
        settings.AI_EMBEDDINGS_ENABLED = True
        calls = []
        monkeypatch.setattr("apps.ai.signals.embed_card.delay", lambda card_id: calls.append(card_id))
        return calls

    def test_creating_a_card_enqueues_after_commit(self, delay, django_capture_on_commit_callbacks):
        column = ColumnFactory()
        with django_capture_on_commit_callbacks(execute=True):
            card = CardService.create_card(column.id, title="Fresh")
        assert delay == [str(card.id)]

    def test_changing_the_title_enqueues(self, delay, django_capture_on_commit_callbacks):
        card = CardFactory()
        delay.clear()
        with django_capture_on_commit_callbacks(execute=True):
            CardService.update_card(card.id, title="Renamed")
        assert delay == [str(card.id)]

    def test_moving_a_card_does_not_enqueue(self, delay, django_capture_on_commit_callbacks):
        source = ColumnFactory()
        dest = ColumnFactory(board=source.board)
        card = CardFactory(column=source)
        delay.clear()
        with django_capture_on_commit_callbacks(execute=True):
            CardService.move_card(card.id, source.id, dest.id, 0)
        assert delay == []

    def test_disabled_setting_never_enqueues(self, delay, settings, django_capture_on_commit_callbacks):
        settings.AI_EMBEDDINGS_ENABLED = False
        with django_capture_on_commit_callbacks(execute=True):
            CardFactory()
        assert delay == []
