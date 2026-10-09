import hashlib
import re

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.ai.evals.retrieval import run_retrieval
from apps.ai.evals.world import build_world, load_dataset
from apps.ai.models import CardEmbedding
from apps.ai.services import embeddings
from apps.workspace.models import Board, Card, Column

pytestmark = pytest.mark.django_db


def bag_of_words(text):
    vector = [0.0] * 384
    for word in re.findall(r"[a-z]+", text.lower()):
        vector[int(hashlib.sha256(word.encode()).hexdigest(), 16) % 384] += 1.0
    norm = sum(x * x for x in vector) ** 0.5 or 1.0
    return [x / norm for x in vector]


@pytest.fixture(autouse=True)
def lexical_embedder(monkeypatch):
    monkeypatch.setattr(embeddings, "embed_passages", lambda texts: [bag_of_words(t) for t in texts])
    monkeypatch.setattr(embeddings, "embed_query", bag_of_words)


def test_the_corpus_is_built_through_the_real_services():
    world = build_world(load_dataset("corpus"))
    assert len(world.cards) == 30 and len(world.boards) == 3
    assert Card.objects.count() == 30 and CardEmbedding.objects.count() == 30
    work_todo = world.columns["work_todo"]
    positions = list(Card.objects.filter(column=work_todo).values_list("position", flat=True))
    assert positions == sorted(positions) and positions[0] == 1000


def test_every_dataset_reference_exists():
    corpus, retrieval, tools = load_dataset("corpus"), load_dataset("retrieval"), load_dataset("tools")
    card_keys = {c["key"] for c in corpus["cards"]}
    column_keys = {c["key"] for b in corpus["boards"] for c in b["columns"]}
    board_keys = {b["key"] for b in corpus["boards"]}
    assert {c["column"] for c in corpus["cards"]} <= column_keys
    assert all(set(q["expected"]) <= card_keys for q in retrieval["queries"])
    for case in tools["cases"]:
        assert case["board"] is None or case["board"] in board_keys
        for check in case["checks"]:
            assert check.get("card", next(iter(card_keys))) in card_keys
            assert check.get("column", next(iter(column_keys))) in column_keys


def test_retrieval_report_has_every_metric():
    world = build_world(load_dataset("corpus"))
    report = run_retrieval(world, load_dataset("retrieval"))
    assert report["queries"] == 28
    assert 0.0 <= report["recall_at_5"] <= 1.0 and 0.0 <= report["mrr"] <= 1.0
    assert report["recall_at_5"] >= report["recall_at_1"]
    assert [row["threshold"] for row in report["threshold_sweep"]] == [0.3, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7]


def test_retrieval_only_ranks_the_eval_corpus_not_real_cards():
    real = Card.objects.create(column=Column.objects.create(board=Board.objects.create(title="Real"), title="C"), title="Send overdue invoices to clients")
    CardEmbedding.objects.create(card=real, embedding=bag_of_words("Send overdue invoices to clients"), text_hash="x", model_name="m")
    world = build_world(load_dataset("corpus"))
    report = run_retrieval(world, {"queries": [{"q": "send overdue invoices to clients", "expected": ["w01"]}], "negatives": []})
    assert report["recall_at_1"] == 1.0
    assert str(real.id) not in world.card_ids


def test_the_command_rolls_everything_back(capsys):
    cards_before = Card.objects.count()
    call_command("run_evals", min_recall=0.0, min_mrr=0.0)
    assert Card.objects.count() == cards_before
    assert CardEmbedding.objects.count() == 0 and Board.objects.count() == 0
    assert "Retrieval (28 queries)" in capsys.readouterr().out


def test_the_command_fails_when_a_threshold_is_missed():
    with pytest.raises(CommandError, match="recall@5"):
        call_command("run_evals", min_recall=1.01, min_mrr=0.0)


def test_live_mode_needs_a_key(settings):
    settings.AI_PROVIDER_KEYS = {}
    settings.AI_API_KEY = ""
    with pytest.raises(CommandError, match="configured model provider"):
        call_command("run_evals", live=True)


def test_results_can_be_written_as_json(tmp_path):
    out = tmp_path / "report.json"
    call_command("run_evals", min_recall=0.0, min_mrr=0.0, json_path=str(out))
    assert '"recall_at_5"' in out.read_text()
