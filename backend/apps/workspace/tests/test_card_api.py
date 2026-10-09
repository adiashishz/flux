import uuid

import pytest
from rest_framework.test import APIClient

from apps.workspace.models import Card

from .factories import CardFactory, ColumnFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_create_card_appends_and_returns_201(client):
    column = ColumnFactory()
    CardFactory(column=column, position=1000)
    response = client.post(f"/api/v1/columns/{column.id}/cards/", {"title": "New"}, format="json")
    assert response.status_code == 201
    assert response.json()["position"] == 2000


def test_create_card_in_unknown_column_is_404(client):
    response = client.post(f"/api/v1/columns/{uuid.uuid4()}/cards/", {"title": "x"}, format="json")
    assert response.status_code == 404


def test_create_card_requires_a_title(client):
    column = ColumnFactory()
    response = client.post(f"/api/v1/columns/{column.id}/cards/", {}, format="json")
    assert response.status_code == 400


def test_get_card_detail(client):
    card = CardFactory(title="Detail")
    response = client.get(f"/api/v1/cards/{card.id}/")
    assert response.status_code == 200
    assert response.json()["title"] == "Detail"


def test_patch_card_updates_content_and_preview(client):
    card = CardFactory()
    response = client.patch(f"/api/v1/cards/{card.id}/", {"content_markdown": "y" * 300}, format="json")
    assert response.status_code == 200
    card.refresh_from_db()
    assert card.content_markdown == "y" * 300
    assert card.content_preview == "y" * 200


def test_patch_unknown_card_is_404(client):
    response = client.patch(f"/api/v1/cards/{uuid.uuid4()}/", {"title": "x"}, format="json")
    assert response.status_code == 404


def test_delete_card_returns_204(client):
    card = CardFactory()
    response = client.delete(f"/api/v1/cards/{card.id}/")
    assert response.status_code == 204
    assert not Card.objects.filter(id=card.id).exists()


def test_move_card_returns_the_new_column(client):
    source = ColumnFactory()
    dest = ColumnFactory(board=source.board)
    card = CardFactory(column=source)
    response = client.post(
        f"/api/v1/cards/{card.id}/move/",
        {"source_column_id": str(source.id), "destination_column_id": str(dest.id), "destination_index": 0},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["column_id"] == str(dest.id)


def test_title_search_matches_case_insensitively(client):
    CardFactory(title="Write Report")
    CardFactory(title="Other")
    response = client.get("/api/v1/search/", {"q": "report"})
    assert [item["title"] for item in response.json()] == ["Write Report"]
