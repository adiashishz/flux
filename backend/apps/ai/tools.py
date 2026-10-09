"""Tools the assistant may call. Every mutation goes through the workspace services, the same
code path as the HTTP API. Deleting is never executed here: it only asks the user to confirm."""
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable

from rest_framework.exceptions import ValidationError

from apps.ai.services.search import semantic_search
from apps.workspace.models import Board, Card, Column
from apps.workspace.selectors.board_selectors import get_board_detail, list_boards
from apps.workspace.services.card_service import CardService

TITLE_MAX = 500
DESCRIPTION_MAX = 2000
MAX_CARDS_PER_COLUMN = 100
UUID_SCHEMA = {"type": "string", "description": "UUID"}


_board_scope = ContextVar("tool_board_scope", default=None)


@contextmanager
def scoped_boards(board_ids):
    """Inside the block, list_boards and get_board only see these boards. The evals use it so a live
    model never sees (or sends to a provider) the boards of your real workspace."""
    token = _board_scope.set(frozenset(str(board_id) for board_id in board_ids))
    try:
        yield
    finally:
        _board_scope.reset(token)


def _in_scope(board_id):
    scope = _board_scope.get()
    return scope is None or str(board_id) in scope


class ToolError(Exception):
    """A problem the model can read and recover from."""


def _uuid(arguments, name):
    try:
        return uuid.UUID(str(arguments[name]))
    except (KeyError, ValueError):
        raise ToolError(f"'{name}' must be a valid UUID taken from earlier tool results.")


def _text(arguments, name, max_length, required=True):
    value = arguments.get(name)
    if value is None:
        if required:
            raise ToolError(f"'{name}' is required.")
        return None
    if not isinstance(value, str) or (required and not value.strip()):
        raise ToolError(f"'{name}' must be a non empty string.")
    if len(value) > max_length:
        raise ToolError(f"'{name}' is too long (max {max_length} characters).")
    return value.strip()


def _card(card_id):
    try:
        return Card.objects.select_related("column__board").get(id=card_id)
    except Card.DoesNotExist:
        raise ToolError("Card not found.")


def _column(column_id):
    try:
        return Column.objects.select_related("board").get(id=column_id)
    except Column.DoesNotExist:
        raise ToolError("Column not found.")


def _card_summary(card):
    return {
        "card_id": str(card.id),
        "title": card.title,
        "column_id": str(card.column_id),
        "column_title": card.column.title,
        "board_id": str(card.column.board_id),
    }


def list_boards_tool(arguments):
    return {
        "boards": [
            {
                "board_id": str(board.id),
                "title": board.title,
                "workspace": board.workspace.title if board.workspace else None,
            }
            for board in list_boards()
            if _in_scope(board.id)
        ]
    }


def get_board_tool(arguments):
    board_id = _uuid(arguments, "board_id")
    try:
        board = get_board_detail(board_id)
    except Board.DoesNotExist:
        raise ToolError("Board not found.")
    if not _in_scope(board.id):
        raise ToolError("Board not found.")
    return {
        "board_id": str(board.id),
        "title": board.title,
        "columns": [
            {
                "column_id": str(column.id),
                "title": column.title,
                "cards": [
                    {"card_id": str(card.id), "title": card.title}
                    for card in list(column.cards.all())[:MAX_CARDS_PER_COLUMN]
                ],
            }
            for column in board.columns.all()
        ],
    }


def search_cards_tool(arguments):
    query = _text(arguments, "query", 200)
    results = semantic_search(query, limit=8)
    return {
        "results": [
            {
                "card_id": item["id"],
                "title": item["title"],
                "preview": item["content_preview"][:120],
                "column_id": item["column_id"],
                "column_title": item["column_title"],
                "board_id": item["board_id"],
                "board_title": item["board_title"],
                "score": item["score"],
            }
            for item in results
        ]
    }


def create_card_tool(arguments):
    column = _column(_uuid(arguments, "column_id"))
    title = _text(arguments, "title", TITLE_MAX)
    description = _text(arguments, "description", DESCRIPTION_MAX, required=False) or ""
    card = CardService.create_card(column.id, title=title, description=description)
    card.column = column
    return _card_summary(card)


def update_card_tool(arguments):
    card = _card(_uuid(arguments, "card_id"))
    changes = {}
    title = _text(arguments, "title", TITLE_MAX, required=False)
    description = _text(arguments, "description", DESCRIPTION_MAX, required=False)
    if title is not None:
        changes["title"] = title
    if description is not None:
        changes["description"] = description
    if not changes:
        raise ToolError("Provide at least one of 'title' or 'description'.")
    updated = CardService.update_card(card.id, **changes)
    updated.column = card.column
    return _card_summary(updated)


def move_card_tool(arguments):
    card = _card(_uuid(arguments, "card_id"))
    destination = _column(_uuid(arguments, "destination_column_id"))
    index = arguments.get("destination_index", 0)
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ToolError("'destination_index' must be an integer of 0 or more.")
    moved = CardService.move_card(card.id, card.column_id, destination.id, index)
    moved.column = destination
    return _card_summary(moved)


def delete_card_tool(arguments):
    card = _card(_uuid(arguments, "card_id"))
    return {
        "requires_confirmation": True,
        "card_id": str(card.id),
        "title": card.title,
        "board_id": str(card.column.board_id),
        "message": "NOT deleted. The user was asked to confirm in the UI. Tell them to confirm there.",
    }


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict
    run: Callable[[dict], dict]


def _schema(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required)}


TOOLS = [
    Tool(
        "list_boards",
        "List every board with its id, title and workspace. Use it to find a board id.",
        _schema({}),
        list_boards_tool,
    ),
    Tool(
        "get_board",
        "Get a board with its columns and cards (ids and titles). Use it before moving or creating cards.",
        _schema({"board_id": UUID_SCHEMA}, ["board_id"]),
        get_board_tool,
    ),
    Tool(
        "search_cards",
        "Semantic search over all cards by meaning. Returns card ids with their column and board.",
        _schema({"query": {"type": "string", "description": "What to look for, in plain words"}}, ["query"]),
        search_cards_tool,
    ),
    Tool(
        "create_card",
        "Create a card at the bottom of a column.",
        _schema(
            {"column_id": UUID_SCHEMA, "title": {"type": "string"}, "description": {"type": "string"}},
            ["column_id", "title"],
        ),
        create_card_tool,
    ),
    Tool(
        "update_card",
        "Change a card's title and/or short description. It cannot edit the card's notes.",
        _schema(
            {"card_id": UUID_SCHEMA, "title": {"type": "string"}, "description": {"type": "string"}},
            ["card_id"],
        ),
        update_card_tool,
    ),
    Tool(
        "move_card",
        "Move a card to a column at a zero based index (0 is the top).",
        _schema(
            {
                "card_id": UUID_SCHEMA,
                "destination_column_id": UUID_SCHEMA,
                "destination_index": {"type": "integer", "minimum": 0},
            },
            ["card_id", "destination_column_id"],
        ),
        move_card_tool,
    ),
    Tool(
        "delete_card",
        "Ask the user to confirm deleting a card. It never deletes by itself.",
        _schema({"card_id": UUID_SCHEMA}, ["card_id"]),
        delete_card_tool,
    ),
]

TOOLS_BY_NAME = {tool.name: tool for tool in TOOLS}


def tool_definitions():
    return [{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in TOOLS]


def run_tool(name, arguments):
    """Returns (ok, data). Errors become data the model can read, never exceptions."""
    tool = TOOLS_BY_NAME.get(name)
    if tool is None:
        return False, {"error": f"Unknown tool '{name}'."}
    if not isinstance(arguments, dict):
        return False, {"error": "Tool arguments must be an object."}
    try:
        return True, tool.run(arguments)
    except ToolError as exc:
        return False, {"error": str(exc)}
    except ValidationError as exc:
        return False, {"error": f"Rejected: {exc.detail}"}
