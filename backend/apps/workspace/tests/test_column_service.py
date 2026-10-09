import uuid

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.workspace.services.column_service import ColumnService

from .factories import BoardFactory, ColumnFactory

pytestmark = pytest.mark.django_db


def test_first_column_gets_the_step_position():
    board = BoardFactory()
    assert ColumnService.create_column(board.id, "Todo").position == 1000


def test_next_column_is_appended():
    board = BoardFactory()
    ColumnFactory(board=board, position=3000)
    assert ColumnService.create_column(board.id, "Next").position == 4000


def test_unknown_board_is_rejected():
    with pytest.raises(ValidationError):
        ColumnService.create_column(uuid.uuid4(), "x")


def test_column_endpoint_still_creates_and_returns_201():
    board = BoardFactory()
    response = APIClient().post(f"/api/v1/boards/{board.id}/columns/", {"title": "Doing"}, format="json")
    assert response.status_code == 201
    assert response.json()["title"] == "Doing" and response.json()["position"] == 1000


def test_column_endpoint_404_for_unknown_board():
    response = APIClient().post(f"/api/v1/boards/{uuid.uuid4()}/columns/", {"title": "x"}, format="json")
    assert response.status_code == 404
