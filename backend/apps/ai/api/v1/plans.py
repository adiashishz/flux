from datetime import timedelta

from django.conf import settings
from django.http import Http404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.ai.models import AssistantRun
from apps.ai.tasks import run_plan_week
from apps.workspace.models import Board

ACTIVE = (AssistantRun.QUEUED, AssistantRun.RUNNING)


class PlanRequestSerializer(serializers.Serializer):
    board_id = serializers.UUIDField()
    focus = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")


def serialize_run(run):
    return {
        "id": str(run.id),
        "kind": run.kind,
        "status": run.status,
        "steps": run.steps,
        "result": run.result,
        "error_message": run.error_message,
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }


class PlanCreateView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

    def post(self, request):
        if not (settings.AI_ENABLED and settings.ANTHROPIC_API_KEY):
            return Response({"detail": "The AI assistant is not enabled."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        serializer = PlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        board = Board.objects.filter(id=data["board_id"]).first()
        if board is None:
            raise Http404

        run = AssistantRun.objects.create(
            board=board, input={"board_id": str(board.id), "focus": data["focus"].strip()}
        )
        try:
            run_plan_week.delay(str(run.id))
        except Exception:
            AssistantRun.objects.filter(id=run.id).update(
                status=AssistantRun.FAILED, error_message="The background queue is not available."
            )
            return Response({"detail": "The background queue is not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(serialize_run(run), status=status.HTTP_202_ACCEPTED)


class RunDetailView(APIView):
    def get(self, request, pk):
        run = AssistantRun.objects.filter(id=pk).first()
        if run is None:
            raise Http404

        stale_before = timezone.now() - timedelta(seconds=settings.AI_RUN_STALE_SECONDS)
        if run.status in ACTIVE and run.updated_at < stale_before:
            AssistantRun.objects.filter(id=run.id, status__in=ACTIVE, updated_at__lt=stale_before).update(
                status=AssistantRun.FAILED, error_message="The run timed out."
            )
            run.refresh_from_db()
        return Response(serialize_run(run))
