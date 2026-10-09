import json
from dataclasses import dataclass, field
from pathlib import Path

from apps.ai.services.indexing import index_card
from apps.workspace.models import Board, Card, Column, Workspace
from apps.workspace.services.card_service import CardService
from apps.workspace.services.column_service import ColumnService

DATASETS = Path(__file__).parent / "datasets"


def load_dataset(name):
    return json.loads((DATASETS / f"{name}.json").read_text())


@dataclass
class World:
    boards: dict = field(default_factory=dict)
    columns: dict = field(default_factory=dict)
    cards: dict = field(default_factory=dict)

    @property
    def card_ids(self):
        return [str(card.id) for card in self.cards.values()]

    def card_key(self, card_id):
        return next((key for key, card in self.cards.items() if str(card.id) == str(card_id)), None)


def build_world(corpus, embed=True):
    """Creates the corpus through the real services. Callers run this inside a transaction they roll back."""
    world = World()
    workspace = Workspace.objects.create(title="Eval workspace")
    for position, spec in enumerate(corpus["boards"], start=1):
        board = Board.objects.create(title=spec["title"], workspace=workspace, position=position * 1000)
        world.boards[spec["key"]] = board
        for column_spec in spec["columns"]:
            world.columns[column_spec["key"]] = ColumnService.create_column(board.id, column_spec["title"])
    for spec in corpus["cards"]:
        column = world.columns[spec["column"]]
        card = CardService.create_card(column.id, title=spec["title"], description=spec["description"])
        world.cards[spec["key"]] = card
        if embed:
            index_card(card.id)
    return world


def snapshot(world):
    """Everything a case could change, keyed by card id."""
    board_ids = [board.id for board in world.boards.values()]
    return {
        str(card.id): (card.title, card.description, str(card.column_id), card.position)
        for card in Card.objects.filter(column__board_id__in=board_ids)
    }


def cards_in_column(world, column_key):
    return list(Card.objects.filter(column=world.columns[column_key]).order_by("position"))


def column_keys(world):
    return {str(column.id): key for key, column in world.columns.items()}
