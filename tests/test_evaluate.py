from recipe_assistant.evaluate import hit_rate, mean_reciprocal_rank


def test_retrieval_metrics():
    rankings = [["a", "b"], ["c", "b"], []]
    expected = [{"a"}, {"b"}, {"z"}]
    assert hit_rate(rankings, expected) == 2 / 3
    assert mean_reciprocal_rank(rankings, expected) == (1 + .5) / 3
