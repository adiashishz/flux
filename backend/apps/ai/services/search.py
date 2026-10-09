from django.conf import settings
from pgvector.django import CosineDistance

from apps.ai.models import CardEmbedding
from apps.ai.services import embeddings


def semantic_search(query, limit=None):
    query = query.strip()
    if not query:
        return []

    query_vector = embeddings.embed_query(query)
    max_distance = 1 - settings.AI_SEARCH_MIN_SCORE
    limit = limit or settings.AI_SEARCH_LIMIT

    rows = (
        CardEmbedding.objects.annotate(distance=CosineDistance("embedding", query_vector))
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
