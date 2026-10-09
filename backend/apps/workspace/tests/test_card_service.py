import uuid

import pytest
from rest_framework.exceptions import ValidationError

from apps.workspace.models import Card
from apps.workspace.services.card_service import CardService

from .factories import CardFactory, ColumnFactory

pytestmark = pytest.mark.django_db


class TestCreateCard:
    def test_first_card_gets_the_step_position(self):
        column = ColumnFactory()
        card = CardService.create_card(column.id, title="First")
        assert card.position == 1000

    def test_next_card_is_appended_after_the_last(self):
        column = ColumnFactory()
        CardFactory(column=column, position=4000)
        card = CardService.create_card(column.id, title="Next", description="d")
        assert card.position == 5000
        assert card.description == "d"

    def test_unknown_column_is_rejected(self):
        with pytest.raises(ValidationError):
            CardService.create_card(uuid.uuid4(), title="Nope")


class TestUpdateCard:
    def test_updates_fields_and_refreshes_updated_at(self):
        card = CardFactory(title="Old")
        before = card.updated_at
        updated = CardService.update_card(card.id, title="New", description="desc")
        updated.refresh_from_db()
        assert (updated.title, updated.description) == ("New", "desc")
        assert updated.updated_at > before

    def test_content_markdown_sets_a_200_character_preview(self):
        card = CardFactory()
        updated = CardService.update_card(card.id, content_markdown="x" * 500)
        assert updated.content_preview == "x" * 200

    def test_unknown_fields_are_rejected(self):
        card = CardFactory()
        with pytest.raises(ValidationError):
            CardService.update_card(card.id, column_id=uuid.uuid4())

    def test_unknown_card_is_rejected(self):
        with pytest.raises(ValidationError):
            CardService.update_card(uuid.uuid4(), title="x")


class TestDeleteCard:
    def test_deletes_the_card(self):
        card = CardFactory()
        CardService.delete_card(card.id)
        assert not Card.objects.filter(id=card.id).exists()

    def test_unknown_card_is_rejected(self):
        with pytest.raises(ValidationError):
            CardService.delete_card(uuid.uuid4())


class TestMoveCard:
    def test_move_to_an_empty_column_uses_the_step(self):
        source = ColumnFactory()
        dest = ColumnFactory(board=source.board)
        card = CardFactory(column=source)
        moved = CardService.move_card(card.id, source.id, dest.id, 0)
        assert (moved.column_id, moved.position) == (dest.id, 1000)

    def test_move_to_the_front_halves_the_first_position(self):
        source = ColumnFactory()
        dest = ColumnFactory(board=source.board)
        CardFactory(column=dest, position=2000)
        card = CardFactory(column=source)
        moved = CardService.move_card(card.id, source.id, dest.id, 0)
        assert moved.position == 1000

    def test_move_between_two_cards_takes_the_midpoint(self):
        column = ColumnFactory()
        CardFactory(column=column, position=1000)
        CardFactory(column=column, position=3000)
        card = CardFactory(column=ColumnFactory(board=column.board))
        moved = CardService.move_card(card.id, card.column_id, column.id, 1)
        assert moved.position == 2000

    def test_move_to_the_end_appends_a_step(self):
        column = ColumnFactory()
        CardFactory(column=column, position=1000)
        card = CardFactory(column=ColumnFactory(board=column.board))
        moved = CardService.move_card(card.id, card.column_id, column.id, 5)
        assert moved.position == 2000

    def test_close_positions_trigger_a_rebalance(self):
        column = ColumnFactory()
        CardFactory(column=column, position=1000)
        CardFactory(column=column, position=1005)
        card = CardFactory(column=ColumnFactory(board=column.board))
        CardService.move_card(card.id, card.column_id, column.id, 1)
        positions = list(Card.objects.filter(column=column).order_by("position").values_list("position", flat=True))
        assert positions == [1000, 2000, 3000]

    def test_wrong_source_column_is_rejected(self):
        card = CardFactory()
        other = ColumnFactory(board=card.column.board)
        with pytest.raises(ValidationError):
            CardService.move_card(card.id, other.id, other.id, 0)

    def test_unknown_destination_is_rejected(self):
        card = CardFactory()
        with pytest.raises(ValidationError):
            CardService.move_card(card.id, card.column_id, uuid.uuid4(), 0)
