from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.services.search import semantic_search


class SemanticSearchView(APIView):
    def get(self, request):
        return Response(semantic_search(request.query_params.get("q", "")))
