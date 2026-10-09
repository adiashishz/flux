from apps.workspace.models import Board


def get_board_detail(board_id):
    return Board.objects.prefetch_related("columns__cards").get(id=board_id)


def list_boards():
    return Board.objects.select_related("workspace").order_by("workspace__title", "position")
