from __future__ import annotations
import os
import sys
import json
import shutil
from pathlib import Path
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

REQUIRED_RATING_COLUMNS = ["userId", "movieId", "rating", "timestamp"]
REQUIRED_MOVIE_COLUMNS = ["movieId", "title", "genres"]


def _spark_session():
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    return (SparkSession.builder.appName("recommendation-preprocessing")
            .config("spark.hadoop.fs.permissions.enabled", "false")
            .config("spark.hadoop.io.native.lib.available", "false")
            .config("spark.hadoop.io.nativeio.enabled", "false")
            .config("spark.driver.memory", "6g")
            .config("spark.sql.shuffle.partitions", "8")
            .getOrCreate())

def _read_csv(spark, path, name):
    if not path.exists():
        raise FileNotFoundError(f"{name} not found: {path}")
    frame = spark.read.option("header", True).option("inferSchema", True).csv(str(path))
    return frame

def _require_columns(frame, required, name):
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")

def _clean_movies(movies):
    _require_columns(movies, REQUIRED_MOVIE_COLUMNS, "movies.csv")
    frame = movies.select("movieId", "title", "genres").dropDuplicates(["movieId"])
    frame = frame.withColumn("movieId", F.col("movieId").cast("long"))
    frame = frame.withColumn("title", F.col("title").cast("string"))
    frame = frame.withColumn("genres", F.coalesce(F.col("genres").cast("string"), F.lit("(no genres listed)")))
    frame = frame.filter(F.col("movieId").isNotNull() & (F.col("movieId") > 0) & F.col("title").isNotNull())
    return frame

def _clean_ratings(ratings, movies):
    _require_columns(ratings, REQUIRED_RATING_COLUMNS, "ratings.csv")
    frame = ratings.select("userId", "movieId", "rating", "timestamp")
    frame = frame.withColumn("userId", F.col("userId").cast("long"))
    frame = frame.withColumn("movieId", F.col("movieId").cast("long"))
    frame = frame.withColumn("rating", F.col("rating").cast("double"))
    frame = frame.withColumn("timestamp", F.col("timestamp").cast("long"))
    frame = frame.filter(
        F.col("userId").isNotNull() & (F.col("userId") > 0) &
        F.col("movieId").isNotNull() & (F.col("movieId") > 0) &
        F.col("rating").isNotNull() & (F.col("rating") >= 0.0) & (F.col("rating") <= 5.0) &
        F.col("timestamp").isNotNull() & (F.col("timestamp") > 0)
    )
    frame = frame.dropDuplicates(["userId", "movieId", "timestamp"])
    window = Window.partitionBy("userId", "movieId").orderBy(F.col("timestamp").desc())
    frame = frame.withColumn("_row_number", F.row_number().over(window))
    frame = frame.filter(F.col("_row_number") == 1).drop("_row_number")
    movie_ids = movies.select("movieId").distinct()
    frame = frame.join(movie_ids, on="movieId", how="inner")
    frame = frame.select("userId", "movieId", "rating", "timestamp")
    if frame.limit(1).count() == 0:
        raise ValueError("Dataset has no usable ratings after validation")
    return frame


def _temporal_cutoffs(frame, test_days, validation_days):
    max_timestamp = frame.agg(F.max("timestamp").alias("max_ts")).collect()[0]["max_ts"]
    if max_timestamp is None:
        raise ValueError("ratings must contain at least one timestamp")
    if validation_days > 0:
        validation_cutoff = int(max_timestamp) - int((test_days + validation_days) * 86400)
        test_cutoff = int(max_timestamp) - int(test_days * 86400)
    else:
        validation_cutoff = int(max_timestamp) - int(test_days * 86400)
        test_cutoff = validation_cutoff
    train = frame.filter(F.col("timestamp") < validation_cutoff)
    validation = frame.filter((F.col("timestamp") >= validation_cutoff) & (F.col("timestamp") < test_cutoff))
    test = frame.filter(F.col("timestamp") >= test_cutoff)
    if train.rdd.isEmpty() or test.rdd.isEmpty():
        quantiles = frame.approxQuantile("timestamp", [0.7, 0.85], 0.0) if validation_days > 0 else frame.approxQuantile("timestamp", [0.8], 0.0)
        if validation_days > 0:
            validation_cutoff = int(quantiles[0])
            test_cutoff = int(quantiles[1])
        else:
            validation_cutoff = test_cutoff = int(quantiles[0])
        train = frame.filter(F.col("timestamp") < validation_cutoff)
        validation = frame.filter((F.col("timestamp") >= validation_cutoff) & (F.col("timestamp") < test_cutoff)) if validation_days > 0 else frame.limit(0)
        test = frame.filter(F.col("timestamp") >= test_cutoff)
    if train.rdd.isEmpty() or test.rdd.isEmpty():
        raise ValueError("Unable to create non-empty chronological train and test partitions")
    return train, validation, test, validation_cutoff, test_cutoff

def _write_csv(frame, path):
    import csv
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    columns = list(frame.columns)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(columns)
        for row in frame.toLocalIterator():
            writer.writerow([row[column] for column in columns])


def run_spark_preprocessing(input_dir, output_dir, test_days=30, validation_days=7, sample=False, sample_fraction=0.01):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    ratings_path = input_dir / "ratings.csv"
    movies_path = input_dir / "movies.csv"
    spark = _spark_session()
    ratings = _read_csv(spark, ratings_path, "ratings.csv")
    movies = _read_csv(spark, movies_path, "movies.csv")
    movies = _clean_movies(movies)
    ratings = _clean_ratings(ratings, movies)
    if sample:
        ratings = ratings.sample(sample_fraction, seed=42)
    train, validation, test, validation_cutoff, test_cutoff = _temporal_cutoffs(ratings, test_days, validation_days)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(train.orderBy("timestamp", "userId", "movieId"), output_dir / "train.csv")
    _write_csv(validation.orderBy("timestamp", "userId", "movieId"), output_dir / "validation.csv")
    _write_csv(test.orderBy("timestamp", "userId", "movieId"), output_dir / "test.csv")
    _write_csv(movies.orderBy("movieId"), output_dir / "movies.csv")
    manifest = {
        "validation_cutoff_timestamp": validation_cutoff,
        "test_cutoff_timestamp": test_cutoff,
        "train_rows": train.count(),
        "validation_rows": validation.count(),
        "test_rows": test.count(),
        "movie_rows": movies.count(),
    }
    (output_dir / "split_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    spark.stop()
    return manifest
