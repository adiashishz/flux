from rest_framework import serializers
from apps.workspace.models import Column
from .card_serializers import CardSerializer


class ColumnSerializer(serializers.ModelSerializer):
    board_id = serializers.UUIDField(source="board.id", read_only=True)
    card_count = serializers.IntegerField(source="cards.count", read_only=True)
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = ["id", "board_id", "title", "position", "card_count", "cards"]
        read_only_fields = ["id", "board_id", "card_count", "cards"]
