import json

from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.ai.services.chat import run_chat

MAX_MESSAGES = 20
MAX_CONTENT_CHARS = 4000


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant"])
    content = serializers.CharField(max_length=MAX_CONTENT_CHARS)


class ChatRequestSerializer(serializers.Serializer):
    messages = ChatMessageSerializer(many=True, allow_empty=False, max_length=MAX_MESSAGES)
    board_id = serializers.UUIDField(required=False)

    def validate_messages(self, messages):
        if messages[-1]["role"] != "user":
            raise serializers.ValidationError("The last message must come from the user.")
        return messages


def _sse(events):
    for event in events:
        yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"


class ChatView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

    def post(self, request):
        if not (settings.AI_ENABLED and settings.ANTHROPIC_API_KEY):
            return Response({"detail": "The AI assistant is not enabled."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        response = StreamingHttpResponse(
            _sse(run_chat(data["messages"], board_id=data.get("board_id"))),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
