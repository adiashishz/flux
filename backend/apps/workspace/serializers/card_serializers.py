from rest_framework import serializers
from apps.workspace.models import Card


class CardSerializer(serializers.ModelSerializer):
    column_id = serializers.UUIDField(source="column.id", read_only=True)

    class Meta:
        model = Card
        fields = ["id", "column_id", "title", "content_preview", "position", "created_at", "updated_at"]
        read_only_fields = ["id", "column_id", "content_preview", "created_at", "updated_at"]


class CardDetailSerializer(serializers.ModelSerializer):
    column_id = serializers.UUIDField(source="column.id", read_only=True)
    column_title = serializers.CharField(source="column.title", read_only=True)

    class Meta:
        model = Card
        fields = ["id", "column_id", "column_title", "title", "content_markdown", "content_preview", "position", "created_at", "updated_at"]
        read_only_fields = ["id", "column_id", "column_title", "content_preview", "created_at", "updated_at"]


class CardMoveSerializer(serializers.Serializer):
    source_column_id = serializers.UUIDField()
    destination_column_id = serializers.UUIDField()
    destination_index = serializers.IntegerField(min_value=0)
