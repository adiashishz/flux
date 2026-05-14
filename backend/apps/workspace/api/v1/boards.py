from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.workspace.models import Board
from apps.workspace.serializers.board_serializers import BoardSerializer, BoardDetailSerializer
from apps.workspace.selectors.board_selectors import get_board_detail


class BoardListView(APIView):
    def get(self, request):
        boards = Board.objects.filter(workspace__isnull=True)
        serializer = BoardSerializer(boards, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BoardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(workspace=None)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BoardDetailView(APIView):
    def _get_board(self, pk):
        try:
            return Board.objects.get(id=pk)
        except Board.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        board = self._get_board(pk)
        serializer = BoardSerializer(board)
        return Response(serializer.data)

    def patch(self, request, pk):
        board = self._get_board(pk)
        serializer = BoardSerializer(board, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        board = self._get_board(pk)
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardNestedDetailView(APIView):
    def get(self, request, pk):
        try:
            board = get_board_detail(pk)
        except Board.DoesNotExist:
            raise Http404
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data)
