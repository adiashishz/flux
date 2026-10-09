from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField


class CardEmbedding(models.Model):
    card = models.OneToOneField(
        "workspace.Card", on_delete=models.CASCADE, primary_key=True, related_name="embedding"
    )
    embedding = VectorField(dimensions=settings.EMBEDDING_DIMENSIONS)
    text_hash = models.CharField(max_length=64)
    model_name = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            HnswIndex(
                name="card_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self):
        return f"Embedding for card {self.card_id}"
