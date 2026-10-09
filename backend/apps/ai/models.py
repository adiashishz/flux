from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField

from apps.core.models import BaseModel


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


class AssistantRun(BaseModel):
    """One background run of an assistant workflow (currently the weekly plan)."""

    QUEUED, RUNNING, SUCCEEDED, FAILED = "queued", "running", "succeeded", "failed"
    STATUS_CHOICES = [(value, value) for value in (QUEUED, RUNNING, SUCCEEDED, FAILED)]
    PLAN_WEEK = "plan_week"

    kind = models.CharField(max_length=40, default=PLAN_WEEK)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=QUEUED)
    board = models.ForeignKey("workspace.Board", null=True, on_delete=models.SET_NULL, related_name="assistant_runs")
    input = models.JSONField(default=dict)
    steps = models.JSONField(default=list)
    result = models.JSONField(null=True, blank=True)
    error_message = models.CharField(max_length=300, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["status", "updated_at"], name="assistant_run_status_idx")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.kind} {self.status} {self.id}"
