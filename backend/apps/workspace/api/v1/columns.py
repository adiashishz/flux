from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.workspace.models import Board, Column
from apps.workspace.serializers.column_serializers import ColumnSerializer


class BoardColumnCreateView(APIView):
    def post(self, request, pk):
        try:
            board = Board.objects.get(id=pk)
        except Board.DoesNotExist:
            raise Http404

        last = Column.objects.filter(board=board).order_by("position").last()
        next_position = (last.position + 1000) if last else 1000

        serializer = ColumnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(board=board, position=next_position)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
