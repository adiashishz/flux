from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.workspace.models import Workspace, Board
from apps.workspace.serializers.workspace_serializers import WorkspaceSerializer, WorkspaceDetailSerializer
from apps.workspace.serializers.board_serializers import BoardSerializer


class WorkspaceListView(APIView):
    def get(self, request):
        workspaces = Workspace.objects.all()
        serializer = WorkspaceSerializer(workspaces, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WorkspaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WorkspaceDetailView(APIView):
    def _get_workspace(self, pk):
        try:
            return Workspace.objects.prefetch_related("boards").get(id=pk)
        except Workspace.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        workspace = self._get_workspace(pk)
        serializer = WorkspaceDetailSerializer(workspace)
        return Response(serializer.data)

    def patch(self, request, pk):
        workspace = self._get_workspace(pk)
        serializer = WorkspaceSerializer(workspace, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        workspace = self._get_workspace(pk)
        workspace.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceBoardCreateView(APIView):
    def post(self, request, pk):
        try:
            workspace = Workspace.objects.get(id=pk)
        except Workspace.DoesNotExist:
            raise Http404
        serializer = BoardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        last = Board.objects.filter(workspace=workspace).order_by("position").last()
        next_position = (last.position + 1000) if last else 1000
        serializer.save(workspace=workspace, position=next_position)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
