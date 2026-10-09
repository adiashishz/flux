from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.workspace.models import Column, Card
from apps.workspace.serializers.card_serializers import CardSerializer, CardDetailSerializer, CardMoveSerializer
from apps.workspace.services.card_service import CardService


class ColumnCardCreateView(APIView):
    def post(self, request, pk):
        if not Column.objects.filter(id=pk).exists():
            raise Http404

        serializer = CardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        card = CardService.create_card(
            column_id=pk,
            title=data["title"],
            description=data.get("description", ""),
        )
        return Response(CardSerializer(card).data, status=status.HTTP_201_CREATED)


class CardDetailView(APIView):
    def _get_card(self, pk):
        try:
            return Card.objects.get(id=pk)
        except Card.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        card = self._get_card(pk)
        serializer = CardDetailSerializer(card)
        return Response(serializer.data)

    def patch(self, request, pk):
        card = self._get_card(pk)
        serializer = CardDetailSerializer(card, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        card = CardService.update_card(card.id, **serializer.validated_data)
        return Response(CardDetailSerializer(card).data)

    def delete(self, request, pk):
        card = self._get_card(pk)
        CardService.delete_card(card.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CardMoveView(APIView):
    def post(self, request, pk):
        try:
            Card.objects.get(id=pk)
        except Card.DoesNotExist:
            raise Http404

        serializer = CardMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        card = CardService.move_card(
            card_id=pk,
            source_column_id=data["source_column_id"],
            dest_column_id=data["destination_column_id"],
            dest_index=data["destination_index"],
        )
        return Response(CardSerializer(card).data)


class SearchView(APIView):
    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response([])

        cards = Card.objects.filter(title__icontains=q).select_related("column__board")[:25]
        results = [
            {
                "id": str(card.id),
                "title": card.title,
                "content_preview": card.content_preview,
                "column_id": str(card.column_id),
                "column_title": card.column.title,
                "board_id": str(card.column.board_id),
                "board_title": card.column.board.title,
            }
            for card in cards
        ]
        return Response(results)
