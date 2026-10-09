import hashlib

from django.conf import settings

from apps.ai.models import CardEmbedding
from apps.ai.services import embeddings
from apps.ai.services.text import build_card_text
from apps.workspace.models import Card

MISSING = "missing"
UNCHANGED = "unchanged"
EMBEDDED = "embedded"


def index_card(card_id):
    """Embed a card unless its text and model are unchanged. Reads the current DB state, so
    a late task can never overwrite a newer embedding with stale text."""
    card = Card.objects.filter(id=card_id).first()
    if card is None:
        return MISSING

    text = build_card_text(card)
    digest = hashlib.sha256(text.encode()).hexdigest()
    model_name = settings.EMBEDDING_MODEL

    existing = CardEmbedding.objects.filter(card_id=card_id).only("text_hash", "model_name").first()
    if existing and existing.text_hash == digest and existing.model_name == model_name:
        return UNCHANGED

    vector = embeddings.embed_passages([text])[0]
    CardEmbedding.objects.update_or_create(
        card_id=card_id,
        defaults={"embedding": vector, "text_hash": digest, "model_name": model_name},
    )
    return EMBEDDED
