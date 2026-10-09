from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.services.providers import provider_status


class StatusView(APIView):
    """Which model the assistant would use and what is missing. Never includes keys."""

    def get(self, request):
        return Response(provider_status())
