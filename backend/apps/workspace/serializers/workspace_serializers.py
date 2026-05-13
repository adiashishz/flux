from rest_framework import serializers
from apps.workspace.models import Workspace
from .board_serializers import BoardSerializer


class WorkspaceSerializer(serializers.ModelSerializer):
    board_count = serializers.IntegerField(source="boards.count", read_only=True)

    class Meta:
        model = Workspace
        fields = ["id", "title", "created_at", "updated_at", "board_count"]
        read_only_fields = ["id", "created_at", "updated_at", "board_count"]


class WorkspaceDetailSerializer(serializers.ModelSerializer):
    board_count = serializers.IntegerField(source="boards.count", read_only=True)
    boards = BoardSerializer(many=True, read_only=True)

    class Meta:
        model = Workspace
        fields = ["id", "title", "created_at", "updated_at", "board_count", "boards"]
        read_only_fields = ["id", "created_at", "updated_at", "board_count", "boards"]
