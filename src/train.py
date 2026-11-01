from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from src.data import load_movielens, temporal_split
from src.recommender import TwoStageBaseline
from src.metrics import recall_at_k, ndcg_at_k, hit_rate_at_k, precision_at_k


def evaluate(model, test, k=10):
    grouped = list(test.groupby("userId"))
    if len(grouped) > 1000:
        import random
        random.seed(42)
        grouped = random.sample(grouped, 1000)
    relevant_by_user = {
        int(uid): set(group.loc[group["rating"] >= 4.0, "movieId"].astype(int))
        for uid, group in grouped
    }
    recalls, ndcgs, hits, precisions = [], [], [], []
    for uid, relevant in relevant_by_user.items():
        if not relevant:
            continue
        recommendations = [x["movie_id"] for x in model.recommend(uid, k=k)]
        recalls.append(recall_at_k(recommendations, relevant, k))
        ndcgs.append(ndcg_at_k(recommendations, relevant, k))
        hits.append(hit_rate_at_k(recommendations, relevant, k))
        precisions.append(precision_at_k(recommendations, relevant, k))
    if not recalls:
        return {"recall_at_k": 0.0, "ndcg_at_k": 0.0, "hit_rate_at_k": 0.0, "precision_at_k": 0.0, "users_evaluated": 0}
    return {
        "recall_at_k": round(sum(recalls) / len(recalls), 6),
        "ndcg_at_k": round(sum(ndcgs) / len(ndcgs), 6),
        "hit_rate_at_k": round(sum(hits) / len(hits), 6),
        "precision_at_k": round(sum(precisions) / len(precisions), 6),
        "users_evaluated": len(recalls),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--test-days", type=int, default=30)
    parser.add_argument("--validation-days", type=int, default=7)
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    if (data_dir / "train.csv").exists() and (data_dir / "test.csv").exists():
        train = pd.read_csv(data_dir / "train.csv")
        test = pd.read_csv(data_dir / "test.csv")
        movies = pd.read_csv(data_dir / "movies.csv")
    else:
        ratings, movies = load_movielens(data_dir)
        train, val, test, _, _ = temporal_split(ratings, args.test_days, args.validation_days)
    model = TwoStageBaseline().fit(train, movies)
    ranker_train = train.sample(n=min(200000, len(train)), random_state=42) if len(train) > 200000 else train
    model.train_ranker(ranker_train)
    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save(model_dir / "recommender.joblib")
    metrics = evaluate(model, test)
    metrics["split"] = "held-out test"
    (model_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print("Saved model to", model_dir / "recommender.joblib")


if __name__ == "__main__":
    main()
