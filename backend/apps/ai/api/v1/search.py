from django.conf import settings
from pgvector.django import CosineDistance
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.models import CardEmbedding
from apps.ai.services import embeddings


class SemanticSearchView(APIView):
    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response([])

        query_vector = embeddings.embed_query(q)
        max_distance = 1 - settings.AI_SEARCH_MIN_SCORE

        rows = (
            CardEmbedding.objects.annotate(distance=CosineDistance("embedding", query_vector))
            .filter(distance__lte=max_distance)
            .select_related("card__column__board")
            .order_by("distance")[: settings.AI_SEARCH_LIMIT]
        )
        return Response(
            [
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
        )
