from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.workspace.models import Board


class BoardService:
    POSITION_STEP = 1000
    REBALANCE_THRESHOLD = 10

    @staticmethod
    @transaction.atomic
    def move_board(board_id, dest_index):
        try:
            board = Board.objects.select_for_update().get(id=board_id)
        except Board.DoesNotExist:
            raise ValidationError({"board_id": "Board not found."})

        # Scope siblings by same workspace (handles personal=null and workspace boards)
        sibling_boards = list(
            Board.objects.filter(workspace=board.workspace)
            .exclude(id=board_id)
            .order_by("position")
            .values_list("id", "position")
        )

        position = BoardService._calculate_position(sibling_boards, dest_index)
        board.position = position
        board.save(update_fields=["position", "updated_at"])

        if BoardService._needs_rebalance(board.workspace_id, board_id):
            BoardService.rebalance_boards(board.workspace_id)
            board.refresh_from_db()

        return board

    @staticmethod
    def _calculate_position(ordered_boards, dest_index):
        step = BoardService.POSITION_STEP

        if not ordered_boards:
            return step

        if dest_index <= 0:
            first_pos = ordered_boards[0][1]
            new_pos = first_pos // 2
            return new_pos if new_pos > 0 else 1

        if dest_index >= len(ordered_boards):
            last_pos = ordered_boards[-1][1]
            return last_pos + step

        before_pos = ordered_boards[dest_index - 1][1]
        after_pos = ordered_boards[dest_index][1]
        return (before_pos + after_pos) // 2

    @staticmethod
    def _needs_rebalance(workspace_id, moved_board_id):
        positions = list(
            Board.objects.filter(workspace_id=workspace_id)
            .order_by("position")
            .values_list("position", flat=True)
        )
        for i in range(1, len(positions)):
            if positions[i] - positions[i - 1] < BoardService.REBALANCE_THRESHOLD:
                return True
        return False

    @staticmethod
    @transaction.atomic
    def rebalance_boards(workspace_id):
        boards = list(
            Board.objects.filter(workspace_id=workspace_id)
            .order_by("position")
            .only("id", "position")
        )
        for i, b in enumerate(boards):
            b.position = (i + 1) * BoardService.POSITION_STEP

        Board.objects.bulk_update(boards, ["position"])
