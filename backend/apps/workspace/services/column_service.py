from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.workspace.models import Board, Column


class ColumnService:
    POSITION_STEP = 1000
    REBALANCE_THRESHOLD = 10

    @staticmethod
    @transaction.atomic
    def create_column(board_id, title):
        try:
            board = Board.objects.select_for_update().get(id=board_id)
        except Board.DoesNotExist:
            raise ValidationError({"board_id": "Board not found."})

        last = Column.objects.filter(board=board).order_by("position").last()
        position = (last.position + ColumnService.POSITION_STEP) if last else ColumnService.POSITION_STEP
        return Column.objects.create(board=board, title=title, position=position)

    @staticmethod
    @transaction.atomic
    def move_column(column_id, board_id, dest_index):
        try:
            column = Column.objects.select_for_update().get(id=column_id)
        except Column.DoesNotExist:
            raise ValidationError({"column_id": "Column not found."})

        if str(column.board_id) != str(board_id):
            raise ValidationError({"board_id": "Column does not belong to this board."})

        sibling_columns = list(
            Column.objects.filter(board_id=board_id)
            .exclude(id=column_id)
            .order_by("position")
            .values_list("id", "position")
        )

        position = ColumnService._calculate_position(sibling_columns, dest_index)
        column.position = position
        column.save(update_fields=["position", "updated_at"])

        if ColumnService._needs_rebalance(board_id, column_id):
            ColumnService.rebalance_board_columns(board_id)
            column.refresh_from_db()

        return column

    @staticmethod
    def _calculate_position(ordered_columns, dest_index):
        step = ColumnService.POSITION_STEP

        if not ordered_columns:
            return step

        if dest_index <= 0:
            first_pos = ordered_columns[0][1]
            new_pos = first_pos // 2
            return new_pos if new_pos > 0 else 1

        if dest_index >= len(ordered_columns):
            last_pos = ordered_columns[-1][1]
            return last_pos + step

        before_pos = ordered_columns[dest_index - 1][1]
        after_pos = ordered_columns[dest_index][1]
        return (before_pos + after_pos) // 2

    @staticmethod
    def _needs_rebalance(board_id, moved_column_id):
        positions = list(
            Column.objects.filter(board_id=board_id)
            .order_by("position")
            .values_list("position", flat=True)
        )
        for i in range(1, len(positions)):
            if positions[i] - positions[i - 1] < ColumnService.REBALANCE_THRESHOLD:
                return True
        return False

    @staticmethod
    @transaction.atomic
    def rebalance_board_columns(board_id):
        columns = list(
            Column.objects.filter(board_id=board_id)
            .order_by("position")
            .only("id", "position")
        )
        for i, col in enumerate(columns):
            col.position = (i + 1) * ColumnService.POSITION_STEP

        Column.objects.bulk_update(columns, ["position"])
