import factory

from apps.workspace.models import Board, Card, Column, Workspace


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workspace

    title = factory.Sequence(lambda n: f"Workspace {n}")


class BoardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Board

    title = factory.Sequence(lambda n: f"Board {n}")
    workspace = factory.SubFactory(WorkspaceFactory)
    position = factory.Sequence(lambda n: (n + 1) * 1000)


class ColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Column

    board = factory.SubFactory(BoardFactory)
    title = factory.Sequence(lambda n: f"Column {n}")
    position = factory.Sequence(lambda n: (n + 1) * 1000)


class CardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Card

    column = factory.SubFactory(ColumnFactory)
    title = factory.Sequence(lambda n: f"Card {n}")
    position = factory.Sequence(lambda n: (n + 1) * 1000)
