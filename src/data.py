
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import pandas as pd

RATING_COLUMNS = ["userId", "movieId", "rating", "timestamp"]
MOVIE_COLUMNS = ["movieId", "title", "genres"]


class DataValidationError(ValueError):
    """Raised when a dataset fails validation."""
    pass


def _require_columns(frame, required, name):
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise DataValidationError(f"{name} is missing columns: {missing}")



def _coerce_ratings(ratings):
    _require_columns(ratings, RATING_COLUMNS, "ratings.csv")
    ratings = ratings[RATING_COLUMNS].copy()
    ratings["userId"] = pd.to_numeric(ratings["userId"], errors="raise").astype("int64")
    ratings["movieId"] = pd.to_numeric(ratings["movieId"], errors="raise").astype("int64")
    ratings["rating"] = pd.to_numeric(ratings["rating"], errors="raise").astype(float)
    ratings["timestamp"] = pd.to_numeric(ratings["timestamp"], errors="raise").astype("int64")

    ratings = ratings[
        (ratings["userId"] > 0)
        & (ratings["movieId"] > 0)
        & (ratings["rating"] >= 0.0)
        & (ratings["rating"] <= 5.0)
        & (ratings["timestamp"] > 0)
    ].copy()

    ratings = ratings.sort_values("timestamp")
    ratings = ratings.drop_duplicates(subset=["userId", "movieId", "timestamp"])
    ratings = ratings.drop_duplicates(subset=["userId", "movieId"], keep="last")
    return ratings.reset_index(drop=True)


def _coerce_movies(movies):
    _require_columns(movies, MOVIE_COLUMNS, "movies.csv")
    movies = movies[MOVIE_COLUMNS].copy()
    movies["movieId"] = pd.to_numeric(movies["movieId"], errors="raise").astype("int64")
    movies["title"] = movies["title"].astype(str)
    movies["genres"] = movies["genres"].fillna("(no genres listed)").astype(str)
    movies = movies.dropna(subset=["movieId", "title"])
    movies = movies[movies["movieId"] > 0]
    movies = movies.drop_duplicates("movieId")
    return movies.sort_values("movieId").reset_index(drop=True)


def load_movielens(input_dir):
    from pathlib import Path
    input_dir = Path(input_dir)
    ratings_path = input_dir / "ratings.csv"
    movies_path = input_dir / "movies.csv"
    if not ratings_path.exists() or not movies_path.exists():
        raise FileNotFoundError("Expected ratings.csv and movies.csv in " + str(input_dir))

    ratings = pd.read_csv(ratings_path)
    movies = pd.read_csv(movies_path)
    ratings = _coerce_ratings(ratings)
    movies = _coerce_movies(movies)

    known_movies = set(movies["movieId"].astype(int))
    ratings = ratings[ratings["movieId"].isin(known_movies)].copy()

    if ratings.empty or movies.empty:
        raise DataValidationError("Dataset has no usable ratings or movies after validation")
    return ratings.sort_values("timestamp").reset_index(drop=True), movies


def temporal_split(ratings, test_days=30, validation_days=7):
    if test_days < 1:
        raise ValueError("test_days must be >= 1")
    if validation_days < 0:
        raise ValueError("validation_days must be >= 0")

    ratings = ratings.sort_values("timestamp").reset_index(drop=True)
    max_ts = int(ratings["timestamp"].max())

    if validation_days > 0:
        val_cutoff = max_ts - int((test_days + validation_days) * 24 * 60 * 60)
        test_cutoff = max_ts - int(test_days * 24 * 60 * 60)
        train = ratings[ratings["timestamp"] < val_cutoff].copy()
        val = ratings[(ratings["timestamp"] >= val_cutoff) & (ratings["timestamp"] < test_cutoff)].copy()
        test = ratings[ratings["timestamp"] >= test_cutoff].copy()
    else:
        test_cutoff = max_ts - int(test_days * 24 * 60 * 60)
        val_cutoff = test_cutoff
        train = ratings[ratings["timestamp"] < test_cutoff].copy()
        val = pd.DataFrame(columns=ratings.columns)
        test = ratings[ratings["timestamp"] >= test_cutoff].copy()

    if train.empty or test.empty:
        unique_ts = sorted(ratings["timestamp"].unique())
        if len(unique_ts) < 3 and validation_days > 0:
            validation_days = 0
            unique_ts = sorted(ratings["timestamp"].unique())
        if len(unique_ts) < 2:
            raise ValueError("Need at least two distinct timestamps for a temporal split")
        if validation_days > 0:
            split1 = max(1, min(len(unique_ts) - 2, int(len(unique_ts) * 0.7)))
            split2 = max(split1 + 1, min(len(unique_ts) - 1, int(len(unique_ts) * 0.85)))
            val_cutoff = int(unique_ts[split1])
            test_cutoff = int(unique_ts[split2])
        else:
            split = max(1, min(len(unique_ts) - 1, int(len(unique_ts) * 0.8)))
            val_cutoff = test_cutoff = int(unique_ts[split])
        train = ratings[ratings["timestamp"] < val_cutoff].copy()
        if validation_days > 0:
            val = ratings[(ratings["timestamp"] >= val_cutoff) & (ratings["timestamp"] < test_cutoff)].copy()
        else:
            val = pd.DataFrame(columns=ratings.columns)
        test = ratings[ratings["timestamp"] >= test_cutoff].copy()

    if train.empty or test.empty:
        raise ValueError("Unable to create non-empty chronological train/test partitions")
    return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True), int(val_cutoff), int(test_cutoff)



def validate_no_leakage(train, test):
    if train.empty or test.empty:
        return True
    return bool(train["timestamp"].max() < test["timestamp"].min())
