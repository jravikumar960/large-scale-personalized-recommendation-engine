from __future__ import annotations
import gzip
import json
from pathlib import Path
import pandas as pd


def load_goodbooks(input_dir):
    """Optional Goodbooks adapter. Returns (ratings, books) or raises FileNotFoundError."""
    input_dir = Path(input_dir)
    ratings_path = input_dir / "ratings.csv"
    books_path = input_dir / "books.csv"
    if not ratings_path.exists() or not books_path.exists():
        raise FileNotFoundError("Goodbooks files not found in " + str(input_dir))
    ratings = pd.read_csv(ratings_path)
    books = pd.read_csv(books_path)
    # Normalize to common schema where possible.
    if "book_id" in books.columns and "movieId" not in books.columns:
        books = books.rename(columns={"book_id": "movieId"})
    if "book_id" in ratings.columns and "movieId" not in ratings.columns:
        ratings = ratings.rename(columns={"book_id": "movieId"})
    if "user_id" in ratings.columns:
        ratings = ratings.rename(columns={"user_id": "userId"})
    return ratings, books


def inspect_amazon_join(review_path, metadata_path, max_rows=100000):
    """Compute join-key overlap without loading everything into memory."""
    review_asins = set()
    review_parents = set()
    n_rev = 0
    with gzip.open(review_path, "rt") as f:
        for line in f:
            if n_rev >= max_rows:
                break
            o = json.loads(line)
            review_asins.add(o.get("asin"))
            review_parents.add(o.get("parent_asin"))
            n_rev += 1
    meta_asins = set()
    n_meta = 0
    with gzip.open(metadata_path, "rt") as f:
        for line in f:
            if n_meta >= max_rows:
                break
            o = json.loads(line)
            meta_asins.add(o.get("asin"))
            n_meta += 1
    return {
        "sampled_reviews": n_rev,
        "sampled_metadata": n_meta,
        "review_asin_count": len(review_asins),
        "meta_asin_count": len(meta_asins),
        "overlap_review_asin": len(review_asins & meta_asins),
        "overlap_review_parent_asin": len(review_parents & meta_asins),
    }
