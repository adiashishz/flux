from django.test.utils import override_settings

from apps.ai.evals import metrics
from apps.ai.services.search import semantic_search

RANKING_DEPTH = 10


def run_retrieval(world, dataset):
    """Ranks the whole corpus for every query (no score cutoff) so recall and cutoffs can be studied."""
    ids = {key: str(card.id) for key, card in world.cards.items()}
    titles = {str(card.id): card.title for card in world.cards.values()}

    def search(query):
        with override_settings(AI_SEARCH_MIN_SCORE=-1.0):
            return semantic_search(query, limit=RANKING_DEPTH, card_ids=world.card_ids)

    rows = []
    for item in dataset["queries"]:
        results = search(item["q"])
        rows.append(
            {
                "query": item["q"],
                "expected": {ids[key] for key in item["expected"]},
                "ranked": [r["id"] for r in results],
                "scores": {r["id"]: r["score"] for r in results},
            }
        )
    negatives = [{r["id"]: r["score"] for r in search(query)} for query in dataset["negatives"]]

    summary = metrics.summarize_retrieval(rows)
    sweep = metrics.threshold_sweep(rows, negatives)
    misses = [
        {
            "query": r["query"],
            "expected": sorted(titles[i] for i in r["expected"]),
            "got": [titles[i] for i in r["ranked"][:3]],
        }
        for r in rows
        if not metrics.hit_at(r["ranked"], r["expected"], 5)
    ]
    return {
        **summary,
        **metrics.score_summary(rows, negatives),
        "threshold_sweep": sweep,
        "suggested_min_score": metrics.suggest_threshold(sweep, summary["recall_at_5"]),
        "misses": misses,
    }
