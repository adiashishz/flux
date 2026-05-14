from rest_framework import serializers
from apps.workspace.models import Board
from .column_serializers import ColumnSerializer


class BoardMoveSerializer(serializers.Serializer):
    destination_index = serializers.IntegerField(min_value=0)


class BoardSerializer(serializers.ModelSerializer):
    column_count = serializers.IntegerField(source="columns.count", read_only=True)
    workspace_id = serializers.UUIDField(source="workspace.id", read_only=True, allow_null=True)

    class Meta:
        model = Board
        fields = ["id", "title", "description", "workspace_id", "position", "created_at", "updated_at", "column_count"]
        read_only_fields = ["id", "workspace_id", "position", "created_at", "updated_at", "column_count"]


class BoardDetailSerializer(serializers.ModelSerializer):
    column_count = serializers.IntegerField(source="columns.count", read_only=True)
    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "created_at", "updated_at", "column_count", "columns"]
        read_only_fields = ["id", "created_at", "updated_at", "column_count", "columns"]
