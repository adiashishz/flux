from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.workspace.models import Board, Column
from apps.workspace.serializers.column_serializers import ColumnSerializer, ColumnMoveSerializer
from apps.workspace.services.column_service import ColumnService


class BoardColumnCreateView(APIView):
    def post(self, request, pk):
        try:
            board = Board.objects.get(id=pk)
        except Board.DoesNotExist:
            raise Http404

        serializer = ColumnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        column = ColumnService.create_column(board.id, serializer.validated_data["title"])
        return Response(ColumnSerializer(column).data, status=status.HTTP_201_CREATED)


class ColumnDetailView(APIView):
    def _get_column(self, pk):
        try:
            return Column.objects.get(id=pk)
        except Column.DoesNotExist:
            raise Http404

    def patch(self, request, pk):
        column = self._get_column(pk)
        serializer = ColumnSerializer(column, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        column = self._get_column(pk)
        column.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ColumnMoveView(APIView):
    def post(self, request, pk):
        try:
            column = Column.objects.get(id=pk)
        except Column.DoesNotExist:
            raise Http404

        serializer = ColumnMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        column = ColumnService.move_column(
            column_id=pk,
            board_id=serializer.validated_data["board_id"],
            dest_index=serializer.validated_data["destination_index"],
        )
        return Response(ColumnSerializer(column).data)
