from apps.workspace.models import Board


def get_board_detail(board_id):
    return Board.objects.prefetch_related("columns__cards").get(id=board_id)
