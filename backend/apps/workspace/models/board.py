from django.db import models
from apps.core.models import BaseModel


class Board(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    workspace = models.ForeignKey(
        "workspace.Workspace",
        on_delete=models.CASCADE,
        related_name="boards",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
