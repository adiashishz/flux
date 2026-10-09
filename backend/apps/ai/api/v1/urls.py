from django.urls import path

from .chat import ChatView
from .plans import PlanCreateView, RunDetailView
from .search import SemanticSearchView

urlpatterns = [
    path("search/", SemanticSearchView.as_view(), name="ai-search"),
    path("chat/", ChatView.as_view(), name="ai-chat"),
    path("plans/", PlanCreateView.as_view(), name="ai-plan-create"),
    path("runs/<uuid:pk>/", RunDetailView.as_view(), name="ai-run-detail"),
]
