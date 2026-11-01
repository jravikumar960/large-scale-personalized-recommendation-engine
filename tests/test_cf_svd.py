import pandas as pd
from pathlib import Path
from src.cf_svd import SvdRetriever, train_svd
def make_artifact(tmp_path):
    train = pd.DataFrame([
        {"userId": 1, "movieId": 10, "rating": 5.0, "timestamp": 1},
        {"userId": 1, "movieId": 20, "rating": 4.0, "timestamp": 2},
        {"userId": 2, "movieId": 10, "rating": 4.5, "timestamp": 3},
        {"userId": 2, "movieId": 30, "rating": 4.0, "timestamp": 4},
    ])
    out = tmp_path / "cf"
    train_svd(train, out, k=1)
    return out, train
def test_load_and_retrieve_excludes_seen(tmp_path):
    out, train = make_artifact(tmp_path)
    r = SvdRetriever(out)
    seen = {10}
    recs = r.retrieve(1, seen, k=2)
    assert all(m not in seen for m in recs)
    assert len(recs) <= 2
def test_unknown_user_fallback(tmp_path):
    out, train = make_artifact(tmp_path)
    r = SvdRetriever(out)
    recs = r.retrieve(999, set(), k=2)
    assert len(recs) == 2
def test_empty_candidate_set(tmp_path):
    out, train = make_artifact(tmp_path)
    r = SvdRetriever(out)
    all_items = set(r.item_ids)
    recs = r.retrieve(1, all_items, k=2)
    assert recs == []
def test_missing_artifact_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        SvdRetriever(tmp_path / "missing")
