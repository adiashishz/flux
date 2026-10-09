from django.urls import path

from .search import SemanticSearchView

urlpatterns = [
    path("search/", SemanticSearchView.as_view(), name="ai-search"),
]
