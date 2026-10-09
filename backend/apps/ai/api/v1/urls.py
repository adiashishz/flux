from django.urls import path

from .chat import ChatView
from .plans import PlanCreateView, RunDetailView
from .search import SemanticSearchView
from .status import StatusView

urlpatterns = [
    path("search/", SemanticSearchView.as_view(), name="ai-search"),
    path("status/", StatusView.as_view(), name="ai-status"),
    path("chat/", ChatView.as_view(), name="ai-chat"),
    path("plans/", PlanCreateView.as_view(), name="ai-plan-create"),
    path("runs/<uuid:pk>/", RunDetailView.as_view(), name="ai-run-detail"),
]
