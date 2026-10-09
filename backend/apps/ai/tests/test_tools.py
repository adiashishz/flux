import uuid

import pytest

from apps.ai.tools import TOOLS, run_tool, tool_definitions
from apps.workspace.models import Card
from apps.workspace.tests.factories import BoardFactory, CardFactory, ColumnFactory

pytestmark = pytest.mark.django_db


def test_every_tool_has_a_valid_definition():
    for definition in tool_definitions():
        assert definition["name"] and definition["description"]
        assert definition["input_schema"]["type"] == "object"
    assert len({tool.name for tool in TOOLS}) == len(TOOLS)


def test_unknown_tool_is_an_error_result():
    ok, data = run_tool("drop_database", {})
    assert not ok
    assert "Unknown tool" in data["error"]


def test_arguments_must_be_an_object():
    ok, data = run_tool("list_boards", ["not", "a", "dict"])
    assert not ok


def test_list_boards_returns_ids_and_workspace():
    board = BoardFactory(title="Roadmap")
    ok, data = run_tool("list_boards", {})
    assert ok
    assert {"board_id": str(board.id), "title": "Roadmap", "workspace": board.workspace.title} in data["boards"]


def test_get_board_returns_columns_with_cards_in_order():
    column = ColumnFactory(title="Todo")
    CardFactory(column=column, title="Second", position=2000)
    CardFactory(column=column, title="First", position=1000)
    ok, data = run_tool("get_board", {"board_id": str(column.board_id)})
    assert ok
    assert [c["title"] for c in data["columns"][0]["cards"]] == ["First", "Second"]


def test_get_board_unknown_id_is_an_error():
    ok, data = run_tool("get_board", {"board_id": str(uuid.uuid4())})
    assert not ok and data["error"] == "Board not found."


def test_malformed_uuid_is_an_error_the_model_can_read():
    ok, data = run_tool("get_board", {"board_id": "not-a-uuid"})
    assert not ok and "valid UUID" in data["error"]


def test_create_card_appends_to_the_column():
    column = ColumnFactory()
    ok, data = run_tool("create_card", {"column_id": str(column.id), "title": " Write docs ", "description": "soon"})
    assert ok
    card = Card.objects.get(id=data["card_id"])
    assert (card.title, card.description, card.position) == ("Write docs", "soon", 1000)
    assert data["board_id"] == str(column.board_id)


@pytest.mark.parametrize("title", ["", "   ", None, 5, "x" * 501])
def test_create_card_rejects_bad_titles(title):
    column = ColumnFactory()
    ok, data = run_tool("create_card", {"column_id": str(column.id), "title": title})
    assert not ok
    assert Card.objects.count() == 0


def test_update_card_changes_title_and_description():
    card = CardFactory(title="Old")
    ok, data = run_tool("update_card", {"card_id": str(card.id), "title": "New"})
    assert ok and data["title"] == "New"
    card.refresh_from_db()
    assert card.title == "New"


def test_update_card_needs_something_to_change():
    card = CardFactory()
    ok, data = run_tool("update_card", {"card_id": str(card.id)})
    assert not ok and "at least one" in data["error"]


def test_update_card_cannot_touch_other_fields():
    card = CardFactory(content_markdown="keep me")
    run_tool("update_card", {"card_id": str(card.id), "title": "T", "content_markdown": "overwritten"})
    card.refresh_from_db()
    assert card.content_markdown == "keep me"


def test_move_card_finds_the_source_column_itself():
    source = ColumnFactory()
    destination = ColumnFactory(board=source.board)
    card = CardFactory(column=source)
    ok, data = run_tool(
        "move_card", {"card_id": str(card.id), "destination_column_id": str(destination.id), "destination_index": 0}
    )
    assert ok and data["column_id"] == str(destination.id)
    card.refresh_from_db()
    assert card.column_id == destination.id


@pytest.mark.parametrize("index", [-1, "0", 1.5, True])
def test_move_card_rejects_bad_indexes(index):
    card = CardFactory()
    ok, data = run_tool(
        "move_card",
        {"card_id": str(card.id), "destination_column_id": str(card.column_id), "destination_index": index},
    )
    assert not ok


def test_delete_card_never_deletes():
    card = CardFactory(title="Precious")
    ok, data = run_tool("delete_card", {"card_id": str(card.id)})
    assert ok and data["requires_confirmation"] is True
    assert data["title"] == "Precious"
    assert Card.objects.filter(id=card.id).exists()


def test_search_cards_wraps_semantic_search(monkeypatch):
    monkeypatch.setattr(
        "apps.ai.tools.semantic_search",
        lambda query, limit: [
            {
                "id": "c1", "title": "Found", "content_preview": "p" * 300, "column_id": "col",
                "column_title": "Todo", "board_id": "b", "board_title": "Board", "score": 0.9,
            }
        ],
    )
    ok, data = run_tool("search_cards", {"query": "anything"})
    assert ok
    assert data["results"][0]["card_id"] == "c1"
    assert len(data["results"][0]["preview"]) == 120


def test_scoped_boards_hide_every_other_board_from_the_model():
    from apps.ai.tools import scoped_boards

    mine, other = BoardFactory(title="Eval"), BoardFactory(title="Private")
    ColumnFactory(board=other)
    with scoped_boards([mine.id]):
        ok, data = run_tool("list_boards", {})
        assert [b["title"] for b in data["boards"]] == ["Eval"]
        ok, data = run_tool("get_board", {"board_id": str(other.id)})
        assert not ok and data["error"] == "Board not found."
    ok, data = run_tool("list_boards", {})
    assert {b["title"] for b in data["boards"]} == {"Eval", "Private"}


def test_the_live_eval_runs_the_model_inside_the_board_scope(monkeypatch):
    """A real model must never be handed the titles of boards outside the eval corpus."""
    from apps.ai.evals.tools import run_case
    from apps.ai.evals.world import build_world, load_dataset
    from apps.ai.services import chat
    from .fakes import FakeProvider, final_message, text_block, tool_use_block

    world = build_world(load_dataset("corpus"), embed=False)
    BoardFactory(title="My Real Private Board")
    provider = FakeProvider(final_message(tool_use_block("t1", "list_boards", {})), final_message(text_block("ok")))
    monkeypatch.setattr(chat, "get_provider", lambda: provider)
    run_case(world, next(c for c in load_dataset("tools")["cases"] if c["id"] == "read-only"))
    sent_back = str(provider.calls[1]["messages"])
    assert "Work" in sent_back and "My Real Private Board" not in sent_back
