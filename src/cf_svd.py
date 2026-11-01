from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds


class SvdRetriever:
    def __init__(self, artifact_dir):
        self.artifact_dir = Path(artifact_dir)
        self.user_ids = json.loads((self.artifact_dir / "user_ids.json").read_text())
        self.item_ids = json.loads((self.artifact_dir / "item_ids.json").read_text())
        self.user_to_idx = {int(u): i for i, u in enumerate(self.user_ids)}
        self.item_to_idx = {int(m): i for i, m in enumerate(self.item_ids)}
        self.user_factors = np.load(self.artifact_dir / "user_factors.npy")
        self.item_factors = np.load(self.artifact_dir / "item_factors.npy")
        self.popularity = json.loads((self.artifact_dir / "popularity.json").read_text()) if (self.artifact_dir / "popularity.json").exists() else {}
        self.global_mean = float(json.loads((self.artifact_dir / "config.json").read_text()).get("global_mean", 3.5)) if (self.artifact_dir / "config.json").exists() else 3.5
    def retrieve(self, user_id, seen, k=200):
        uid = self.user_to_idx.get(int(user_id))
        if uid is None:
            # cold-start fallback to popularity
            cands = [int(m) for m in self.item_ids]
            cands.sort(key=lambda m: self.popularity.get(str(m), self.global_mean), reverse=True)
            return [m for m in cands if m not in seen][:k]
        scores = self.user_factors[uid] @ self.item_factors.T
        order = np.argsort(scores)[::-1]
        out = []
        for i in order:
            mid = int(self.item_ids[i])
            if mid in seen:
                continue
            out.append(mid)
            if len(out) >= k:
                break
        return out


def train_svd(train_df, output_dir, k=38):
    tr = train_df[train_df.rating >= 4].copy()
    users = tr.userId.unique()
    items = tr.movieId.unique()
    uid = {int(u): i for i, u in enumerate(users)}
    iid = {int(m): i for i, m in enumerate(items)}
    rows = tr.userId.map(lambda x: uid[int(x)])
    cols = tr.movieId.map(lambda x: iid[int(x)])
    R = csr_matrix((tr.rating.to_numpy(dtype=np.float32), (rows, cols)), shape=(len(users), len(items)))
    U, s, Vt = svds(R, k=k)
    user_factors = (U * s).astype(np.float32)
    item_factors = Vt.T.astype(np.float32)
    popularity = {str(int(m)): float(v) for m, v in train_df.groupby("movieId").rating.mean().items()}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "user_factors.npy", user_factors)
    np.save(out / "item_factors.npy", item_factors)
    (out / "user_ids.json").write_text(json.dumps([int(x) for x in users]), encoding="utf-8")
    (out / "item_ids.json").write_text(json.dumps([int(x) for x in items]), encoding="utf-8")
    (out / "popularity.json").write_text(json.dumps(popularity), encoding="utf-8")
    (out / "config.json").write_text(json.dumps({"k": k, "threshold": 4.0, "weighting": "rating", "global_mean": float(train_df.rating.mean())}), encoding="utf-8")
    return user_factors, item_factors, users, items
