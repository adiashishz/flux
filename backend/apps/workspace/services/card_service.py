from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.workspace.models import Card, Column


class CardService:
    POSITION_STEP = 1000
    REBALANCE_THRESHOLD = 10
    PREVIEW_LENGTH = 200
    UPDATABLE_FIELDS = ("title", "description", "content_markdown", "position")

    @staticmethod
    @transaction.atomic
    def create_card(column_id, title, description=""):
        try:
            column = Column.objects.select_for_update().get(id=column_id)
        except Column.DoesNotExist:
            raise ValidationError({"column_id": "Column not found."})

        last = Card.objects.filter(column=column).order_by("position").last()
        position = (last.position + CardService.POSITION_STEP) if last else CardService.POSITION_STEP

        return Card.objects.create(column=column, title=title, description=description, position=position)

    @staticmethod
    @transaction.atomic
    def update_card(card_id, **fields):
        try:
            card = Card.objects.select_for_update().get(id=card_id)
        except Card.DoesNotExist:
            raise ValidationError({"card_id": "Card not found."})

        unknown = set(fields) - set(CardService.UPDATABLE_FIELDS)
        if unknown:
            raise ValidationError({field: "This field cannot be updated." for field in unknown})

        for name, value in fields.items():
            setattr(card, name, value)

        update_fields = list(fields)
        if "content_markdown" in fields:
            card.content_preview = fields["content_markdown"][: CardService.PREVIEW_LENGTH]
            update_fields.append("content_preview")

        card.save(update_fields=[*update_fields, "updated_at"])
        return card

    @staticmethod
    @transaction.atomic
    def delete_card(card_id):
        try:
            card = Card.objects.select_for_update().get(id=card_id)
        except Card.DoesNotExist:
            raise ValidationError({"card_id": "Card not found."})
        card.delete()

    @staticmethod
    @transaction.atomic
    def move_card(card_id, source_column_id, dest_column_id, dest_index):
        try:
            card = Card.objects.select_for_update().get(id=card_id)
        except Card.DoesNotExist:
            raise ValidationError({"card_id": "Card not found."})

        if str(card.column_id) != str(source_column_id):
            raise ValidationError({"source_column_id": "Card does not belong to source column."})

        try:
            dest_column = Column.objects.get(id=dest_column_id)
        except Column.DoesNotExist:
            raise ValidationError({"destination_column_id": "Destination column not found."})

        dest_cards = list(
            Card.objects.filter(column=dest_column)
            .exclude(id=card_id)
            .order_by("position")
            .values_list("id", "position")
        )

        position = CardService._calculate_position(dest_cards, dest_index)

        card.column = dest_column
        card.position = position
        card.save(update_fields=["column", "position", "updated_at"])

        if CardService._needs_rebalance(dest_column.id, card.id):
            CardService.rebalance_column(dest_column.id)
            card.refresh_from_db()

        return card

    @staticmethod
    def _calculate_position(ordered_cards, dest_index):
        step = CardService.POSITION_STEP

        if not ordered_cards:
            return step

        if dest_index <= 0:
            first_pos = ordered_cards[0][1]
            new_pos = first_pos // 2
            return new_pos if new_pos > 0 else 1

        if dest_index >= len(ordered_cards):
            last_pos = ordered_cards[-1][1]
            return last_pos + step

        before_pos = ordered_cards[dest_index - 1][1]
        after_pos = ordered_cards[dest_index][1]
        return (before_pos + after_pos) // 2

    @staticmethod
    def _needs_rebalance(column_id, moved_card_id):
        cards = list(
            Card.objects.filter(column_id=column_id)
            .order_by("position")
            .values_list("position", flat=True)
        )
        for i in range(1, len(cards)):
            if cards[i] - cards[i - 1] < CardService.REBALANCE_THRESHOLD:
                return True
        return False

    @staticmethod
    @transaction.atomic
    def rebalance_column(column_id):
        cards = list(
            Card.objects.filter(column_id=column_id)
            .order_by("position")
            .only("id", "position")
        )
        for i, card in enumerate(cards):
            card.position = (i + 1) * CardService.POSITION_STEP

        Card.objects.bulk_update(cards, ["position"])
