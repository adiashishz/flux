from django.urls import path
from .boards import BoardListView, BoardDetailView, BoardNestedDetailView
from .columns import BoardColumnCreateView, ColumnDetailView
from .cards import ColumnCardCreateView, CardDetailView, CardMoveView, SearchView

urlpatterns = [
    path("boards/", BoardListView.as_view(), name="board-list"),
    path("boards/<uuid:pk>/", BoardDetailView.as_view(), name="board-detail"),
    path("boards/<uuid:pk>/detail/", BoardNestedDetailView.as_view(), name="board-nested-detail"),
    path("boards/<uuid:pk>/columns/", BoardColumnCreateView.as_view(), name="board-column-create"),
    path("columns/<uuid:pk>/", ColumnDetailView.as_view(), name="column-detail"),
    path("columns/<uuid:pk>/cards/", ColumnCardCreateView.as_view(), name="column-card-create"),
    path("cards/<uuid:pk>/", CardDetailView.as_view(), name="card-detail"),
    path("cards/<uuid:pk>/move/", CardMoveView.as_view(), name="card-move"),
    path("search/", SearchView.as_view(), name="search"),
]
