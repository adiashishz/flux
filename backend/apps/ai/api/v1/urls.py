from django.urls import path

from .chat import ChatView
from .search import SemanticSearchView

urlpatterns = [
    path("search/", SemanticSearchView.as_view(), name="ai-search"),
    path("chat/", ChatView.as_view(), name="ai-chat"),
]
