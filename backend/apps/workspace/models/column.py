from django.db import models
from apps.core.models import BaseModel


class Column(BaseModel):
    board = models.ForeignKey("workspace.Board", on_delete=models.CASCADE, related_name="columns")
    title = models.CharField(max_length=255)
    position = models.IntegerField(default=1000)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.board.title} / {self.title}"
