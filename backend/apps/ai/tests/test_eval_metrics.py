from apps.ai.evals import metrics


def row(ranked, expected, scores=None):
    return {"ranked": ranked, "expected": set(expected), "scores": scores or {item: 1 - i / 10 for i, item in enumerate(ranked)}}


def test_reciprocal_rank():
    assert metrics.reciprocal_rank(["a", "b", "c"], {"b"}) == 0.5
    assert metrics.reciprocal_rank(["a", "b"], {"z"}) == 0.0
    assert metrics.reciprocal_rank(["a", "b"], {"b", "a"}) == 1.0


def test_hit_at_respects_k():
    assert metrics.hit_at(["a", "b", "c"], {"c"}, 3)
    assert not metrics.hit_at(["a", "b", "c"], {"c"}, 2)


def test_summary_averages_over_queries():
    rows = [row(["a", "b"], {"a"}), row(["x", "a"], {"a"}), row(["x", "y"], {"a"})]
    summary = metrics.summarize_retrieval(rows)
    assert summary["queries"] == 3
    assert summary["recall_at_1"] == 1 / 3
    assert summary["recall_at_5"] == 2 / 3
    assert round(summary["mrr"], 4) == round((1 + 0.5 + 0) / 3, 4)


def test_threshold_sweep_trades_recall_for_fewer_unrelated_answers():
    rows = [row(["a"], {"a"}, {"a": 0.9}), row(["b"], {"b"}, {"b": 0.5})]
    negatives = [{"n": 0.6}, {"n": 0.3}]
    sweep = {s["threshold"]: s for s in metrics.threshold_sweep(rows, negatives, thresholds=(0.4, 0.7))}
    assert sweep[0.4]["recall_at_5"] == 1.0 and sweep[0.4]["unrelated_answered"] == "1/2"
    assert sweep[0.7]["recall_at_5"] == 0.5 and sweep[0.7]["unrelated_answered"] == "0/2"


def test_a_relevant_card_below_the_cutoff_does_not_count_as_a_hit():
    rows = [row(["wrong", "right"], {"right"}, {"wrong": 0.9, "right": 0.4})]
    assert metrics.threshold_sweep(rows, [], thresholds=(0.5,))[0]["recall_at_5"] == 0.0


def test_suggested_threshold_is_the_highest_one_that_keeps_recall():
    sweep = [
        {"threshold": 0.5, "recall_at_5": 1.0},
        {"threshold": 0.6, "recall_at_5": 0.97},
        {"threshold": 0.7, "recall_at_5": 0.8},
    ]
    assert metrics.suggest_threshold(sweep, baseline_recall=1.0, tolerance=0.04) == 0.6
    assert metrics.suggest_threshold([{"threshold": 0.9, "recall_at_5": 0.1}], 1.0) is None


def test_score_summary_uses_medians():
    rows = [row(["a"], {"a"}, {"a": 0.8}), row(["b"], {"b"}, {"b": 0.6})]
    summary = metrics.score_summary(rows, [{"n": 0.5}, {"n": 0.7}])
    assert summary == {"median_relevant_score": 0.7, "median_best_unrelated_score": 0.6}
