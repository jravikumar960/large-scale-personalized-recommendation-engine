from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.cf_svd import SvdRetriever
from src.metrics import recall_at_k, ndcg_at_k, hit_rate_at_k, precision_at_k


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--model-dir", default="models/cf_svd")
    parser.add_argument("--output", default="models/cf_svd_validation_metrics.json")
    parser.add_argument("--users", type=int, default=500)
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    train = pd.read_csv(data_dir / "train.csv")
    validation = pd.read_csv(data_dir / "validation.csv")
    retriever = SvdRetriever(args.model_dir)
    eligible = [u for u in validation.userId.unique() if ((validation.userId == u) & (validation.rating >= 4)).any()][:args.users]
    seen_map = {int(u): set(g.movieId.astype(int)) for u, g in train[train.userId.isin(eligible)].groupby("userId")}
    recalls = []
    recalls20 = []
    ndcgs = []
    hits = []
    precisions = []
    for user_id in eligible:
        relevant = set(validation.loc[(validation.userId == user_id) & (validation.rating >= 4), "movieId"].astype(int))
        if not relevant:
            continue
        recommended = retriever.retrieve(int(user_id), seen_map.get(int(user_id), set()), 20)
        recalls.append(recall_at_k(recommended, relevant, 10))
        recalls20.append(recall_at_k(recommended, relevant, 20))
        ndcgs.append(ndcg_at_k(recommended, relevant, 10))
        hits.append(hit_rate_at_k(recommended, relevant, 10))
        precisions.append(precision_at_k(recommended, relevant, 10))
    result = {
        "candidate_set": "cf_svd item vocabulary",
        "relevance": "rating >= 4",
        "users": len(recalls),
        "cf_svd": {
            "recall@10": round(float(sum(recalls) / len(recalls)), 6) if recalls else 0.0,
            "recall@20": round(float(sum(recalls20) / len(recalls20)), 6) if recalls20 else 0.0,
            "ndcg@10": round(float(sum(ndcgs) / len(ndcgs)), 6) if ndcgs else 0.0,
            "hit_rate@10": round(float(sum(hits) / len(hits)), 6) if hits else 0.0,
            "precision@10": round(float(sum(precisions) / len(precisions)), 6) if precisions else 0.0,
        },
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
