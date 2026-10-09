from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from pgvector.django import CosineDistance

from apps.ai.models import CardEmbedding
from apps.ai.services import embeddings


_scope = ContextVar("semantic_search_scope", default=None)


@contextmanager
def scoped_search(card_ids):
    """Limit every semantic_search call inside the block to these cards (used by the evals)."""
    token = _scope.set(frozenset(str(card_id) for card_id in card_ids))
    try:
        yield
    finally:
        _scope.reset(token)


def semantic_search(query, limit=None, card_ids=None):
    query = query.strip()
    if not query:
        return []

    query_vector = embeddings.embed_query(query)
    max_distance = 1 - settings.AI_SEARCH_MIN_SCORE
    limit = limit or settings.AI_SEARCH_LIMIT

    scope = _scope.get() if card_ids is None else frozenset(str(card_id) for card_id in card_ids)
    candidates = CardEmbedding.objects.all() if scope is None else CardEmbedding.objects.filter(card_id__in=scope)
    rows = (
        candidates.annotate(distance=CosineDistance("embedding", query_vector))
        .filter(distance__lte=max_distance)
        .select_related("card__column__board")
        .order_by("distance")[:limit]
    )
    return [
        {
            "id": str(row.card_id),
            "title": row.card.title,
            "content_preview": row.card.content_preview,
            "column_id": str(row.card.column_id),
            "column_title": row.card.column.title,
            "board_id": str(row.card.column.board_id),
            "board_title": row.card.column.board.title,
            "score": round(1 - row.distance, 4),
        }
        for row in rows
    ]
