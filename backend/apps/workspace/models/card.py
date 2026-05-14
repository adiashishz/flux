from django.db import models
from apps.core.models import BaseModel


class Card(BaseModel):
    column = models.ForeignKey("workspace.Column", on_delete=models.CASCADE, related_name="cards")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    content_markdown = models.TextField(blank=True)
    content_preview = models.TextField(blank=True)
    position = models.IntegerField(default=1000)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.title
