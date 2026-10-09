from statistics import median

DEFAULT_THRESHOLDS = (0.3, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7)


def reciprocal_rank(ranked, expected):
    for position, item in enumerate(ranked, start=1):
        if item in expected:
            return 1 / position
    return 0.0


def hit_at(ranked, expected, k):
    return any(item in expected for item in ranked[:k])


def summarize_retrieval(rows):
    """rows: dicts with `ranked` (ids best first) and `expected` (set of ids)."""
    total = len(rows)
    return {
        "queries": total,
        "recall_at_1": sum(hit_at(r["ranked"], r["expected"], 1) for r in rows) / total,
        "recall_at_5": sum(hit_at(r["ranked"], r["expected"], 5) for r in rows) / total,
        "mrr": sum(reciprocal_rank(r["ranked"], r["expected"]) for r in rows) / total,
    }


def threshold_sweep(rows, negatives, thresholds=DEFAULT_THRESHOLDS):
    """What a score cutoff would do: recall@5 on real queries versus how many unrelated
    queries still get an answer. rows carry `scores` (id -> score); negatives are score maps."""
    sweep = []
    for cutoff in thresholds:
        hits = sum(
            any(item in r["expected"] and r["scores"][item] >= cutoff for item in r["ranked"][:5]) for r in rows
        )
        answered = sum(any(score >= cutoff for score in scores.values()) for scores in negatives)
        sweep.append(
            {
                "threshold": cutoff,
                "recall_at_5": hits / len(rows),
                "unrelated_answered": f"{answered}/{len(negatives)}",
                "unrelated_answered_rate": answered / len(negatives) if negatives else 0.0,
            }
        )
    return sweep


def score_summary(rows, negatives):
    relevant = [r["scores"][item] for r in rows for item in r["ranked"] if item in r["expected"]]
    unrelated_best = [max(scores.values()) for scores in negatives if scores]
    return {
        "median_relevant_score": round(median(relevant), 3) if relevant else None,
        "median_best_unrelated_score": round(median(unrelated_best), 3) if unrelated_best else None,
    }


def suggest_threshold(sweep, baseline_recall, tolerance=0.04):
    """Highest cutoff that keeps recall@5 within `tolerance` of having no cutoff at all."""
    keeping = [row["threshold"] for row in sweep if row["recall_at_5"] >= baseline_recall - tolerance]
    return max(keeping) if keeping else None
