from datetime import date

from apps.workspace.models import Board

SYSTEM_PROMPT = """You are the assistant inside Flux, a kanban workspace (workspaces, boards, columns, cards).

How to work:
- Use the tools to read and change the workspace. Never invent ids: take them from tool results.
- Look before you act: get_board or search_cards first, then create_card, update_card or move_card.
- You can change a card's title and description, but you cannot edit its notes.
- You can never delete directly. delete_card only asks the user to confirm, so say that you asked.
- If a request is ambiguous (several matching cards or columns), ask a short question instead of guessing.
- Keep replies short and plain. After changing something, say exactly what you changed.
Today is {today}."""


def build_system_prompt(board_id=None):
    prompt = SYSTEM_PROMPT.format(today=date.today().isoformat())
    if board_id:
        board = Board.objects.filter(id=board_id).only("title").first()
        if board:
            prompt += f"\nThe user is currently viewing the board '{board.title}' (board_id {board.id})."
    return prompt
