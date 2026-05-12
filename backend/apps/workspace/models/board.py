from django.db import models
from apps.core.models import BaseModel


class Board(BaseModel):
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
