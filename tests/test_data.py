import pandas as pd
from src.data import temporal_split, validate_no_leakage
def test_temporal_split_no_leakage():
    ratings = pd.DataFrame([
        {"userId":1,"movieId":1,"rating":5.0,"timestamp":1},
        {"userId":1,"movieId":2,"rating":4.0,"timestamp":2},
        {"userId":2,"movieId":1,"rating":3.0,"timestamp":3},
        {"userId":2,"movieId":2,"rating":4.5,"timestamp":4},
    ])
    train, val, test, vc, tc = temporal_split(ratings, test_days=1, validation_days=0)
    assert validate_no_leakage(train, test)
    assert train.timestamp.max() < test.timestamp.min()
def test_metrics_deterministic():
    from src.metrics import recall_at_k, ndcg_at_k, hit_rate_at_k, precision_at_k
    rec = [1,2,3]
    rel = {2,3}
    assert recall_at_k(rec, rel, 3) == 1.0
    assert hit_rate_at_k(rec, rel, 3) == 1.0
    assert precision_at_k(rec, rel, 3) == 2/3
    assert 0 <= ndcg_at_k(rec, rel, 3) <= 1
