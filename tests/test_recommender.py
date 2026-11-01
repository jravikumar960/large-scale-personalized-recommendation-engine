import pandas as pd
from src.recommender import TwoStageBaseline


def sample_data():
    movies = pd.DataFrame([
        {"movieId": 1, "title": "Space", "genres": "Sci-Fi|Action"},
        {"movieId": 2, "title": "Funny", "genres": "Comedy"},
        {"movieId": 3, "title": "Space 2", "genres": "Sci-Fi"},
        {"movieId": 4, "title": "Drama", "genres": "Drama"},
    ])
    ratings = pd.DataFrame([
        {"userId": 1, "movieId": 1, "rating": 5.0, "timestamp": 1},
        {"userId": 1, "movieId": 3, "rating": 4.5, "timestamp": 2},
        {"userId": 2, "movieId": 2, "rating": 4.5, "timestamp": 3},
        {"userId": 2, "movieId": 4, "rating": 3.0, "timestamp": 4},
        {"userId": 3, "movieId": 1, "rating": 4.0, "timestamp": 5},
        {"userId": 3, "movieId": 2, "rating": 3.5, "timestamp": 6},
    ])
    return ratings, movies


def test_known_user_does_not_get_seen_movies():
    ratings, movies = sample_data()
    model = TwoStageBaseline().fit(ratings, movies)
    results = model.recommend(1, k=3)
    assert all(item["movie_id"] not in {1, 3} for item in results)


def test_unknown_user_gets_popularity_fallback():
    ratings, movies = sample_data()
    model = TwoStageBaseline().fit(ratings, movies)
    results = model.recommend(999, k=2)
    assert len(results) == 2
    assert all("title" in item and "score" in item for item in results)


def test_k_validation():
    ratings, movies = sample_data()
    model = TwoStageBaseline().fit(ratings, movies)
    try:
        model.recommend(1, k=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid k to raise ValueError")
