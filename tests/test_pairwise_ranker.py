import os
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
import numpy as np
import pandas as pd
import pytest
from src.pairwise_ranker import _feature_vector, build_pairwise_examples, load_pairwise_ranker, score_pairwise_ranker
from src.recommender import TwoStageBaseline


def test_feature_vector_shape():
    train = pd.DataFrame([
        {"userId": 1, "movieId": 10, "rating": 5.0, "timestamp": 1},
        {"userId": 1, "movieId": 20, "rating": 2.0, "timestamp": 2},
    ])
    movies = pd.DataFrame([
        {"movieId": 10, "title": "A", "genres": "Action"},
        {"movieId": 20, "title": "B", "genres": "Drama"},
    ])
    model = TwoStageBaseline().fit(train, movies)
    features = _feature_vector(model, 1, 10)
    assert features.shape == (5,)
    assert features[3] == 1.0
    unknown_features = _feature_vector(model, 999, 999)
    assert unknown_features.shape == (5,)
    assert unknown_features[3] == 0.0
    assert unknown_features[4] == 0.0


def test_build_pairwise_examples():
    train = pd.DataFrame([
        {"userId": 1, "movieId": 10, "rating": 5.0, "timestamp": 1},
        {"userId": 1, "movieId": 20, "rating": 2.0, "timestamp": 2},
        {"userId": 2, "movieId": 10, "rating": 4.0, "timestamp": 3},
        {"userId": 2, "movieId": 30, "rating": 2.5, "timestamp": 4},
    ])
    movies = pd.DataFrame([
        {"movieId": 10, "title": "A", "genres": "Action"},
        {"movieId": 20, "title": "B", "genres": "Drama"},
        {"movieId": 30, "title": "C", "genres": "Comedy"},
    ])
    model = TwoStageBaseline().fit(train, movies)
    positive_features, negative_features, pairs = build_pairwise_examples(model, train, sample_size=10, seed=42)
    assert positive_features.shape[1] == 5
    assert negative_features.shape == positive_features.shape
    assert len(pairs) <= 10
    assert all(int(user_id) in set(train.userId) for user_id, _, _ in pairs)


def test_pairwise_ranker_loads_and_is_deterministic():
    model = load_pairwise_ranker("models/pairwise_ranker/pairwise_ranker.keras")
    features = np.asarray([[4.0, 3.5, 2.0, 1.0, 0.5], [1.0, 1.0, 1.0, 0.0, 0.0]], dtype="float32")
    first = score_pairwise_ranker(model, features)
    second = score_pairwise_ranker(model, features)
    assert first.shape == (2,)
    assert np.allclose(first, second)
    assert np.all(np.isfinite(first))


def test_pairwise_ranker_missing_file():
    with pytest.raises((FileNotFoundError, ValueError, OSError)):
        load_pairwise_ranker("models/does_not_exist.keras")
