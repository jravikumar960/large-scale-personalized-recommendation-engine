from src.metrics import recall_at_k, hit_rate_at_k, ndcg_at_k


def test_recall_at_k():
    assert recall_at_k([1, 2, 3], {2, 4}, 2) == 0.5


def test_hit_rate_at_k():
    assert hit_rate_at_k([1, 2], {2}, 2) == 1.0
    assert hit_rate_at_k([1, 3], {2}, 2) == 0.0


def test_ndcg_at_k_is_bounded():
    value = ndcg_at_k([2, 1, 3], {2, 3}, 3)
    assert 0.0 <= value <= 1.0
