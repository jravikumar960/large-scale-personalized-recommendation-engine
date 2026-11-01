
import pytest
from pathlib import Path
import pandas as pd
pyspark = pytest.importorskip("pyspark")
from src.spark_pipeline import run_spark_preprocessing
def make_input(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    ratings = pd.DataFrame([
        {"userId": 1, "movieId": 10, "rating": 5.0, "timestamp": 1},
        {"userId": 1, "movieId": 20, "rating": 4.0, "timestamp": 2},
        {"userId": 2, "movieId": 10, "rating": 3.0, "timestamp": 3},
        {"userId": 2, "movieId": 20, "rating": 4.5, "timestamp": 4},
        {"userId": 1, "movieId": 10, "rating": 2.0, "timestamp": 5},
        {"userId": 3, "movieId": 999, "rating": 4.0, "timestamp": 6},
        {"userId": 0, "movieId": 10, "rating": 4.0, "timestamp": 7},
    ])
    movies = pd.DataFrame([
        {"movieId": 10, "title": "A", "genres": "Action"},
        {"movieId": 20, "title": "B", "genres": "Drama"},
    ])
    ratings.to_csv(input_dir / "ratings.csv", index=False)
    movies.to_csv(input_dir / "movies.csv", index=False)
    return input_dir

def test_spark_preprocessing(tmp_path):
    input_dir = make_input(tmp_path)
    output_dir = tmp_path / "output"
    manifest = run_spark_preprocessing(input_dir, output_dir, test_days=1, validation_days=0)
    assert (output_dir / "train.csv").is_file()
    assert (output_dir / "test.csv").is_file()
    assert (output_dir / "movies.csv").is_file()
    train = pd.read_csv(output_dir / "train.csv")
    test = pd.read_csv(output_dir / "test.csv")
    assert list(train.columns) == ["userId", "movieId", "rating", "timestamp"]
    assert train.timestamp.max() < test.timestamp.min()
    assert 999 not in set(train.movieId) | set(test.movieId)
    assert 0 not in set(train.userId) | set(test.userId)
    assert not train.duplicated(["userId", "movieId"]).any()
    assert manifest["train_rows"] + manifest["test_rows"] == 4

def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_spark_preprocessing(tmp_path / "missing", tmp_path / "out")
