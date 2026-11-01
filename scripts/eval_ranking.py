import os
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
import json
import numpy as np
import pandas as pd
from src.recommender import TwoStageBaseline
from src.deep_ranker import load_deep_ranker
from src.metrics import recall_at_k, ndcg_at_k, hit_rate_at_k, precision_at_k
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")
model = TwoStageBaseline.load("models/recommender.joblib")
deep_model = load_deep_ranker("models/deep_ranker/deep_ranker.keras")
class Adapter:
    def predict(self, feats):
        X = feats[["popularity_score", "genre_affinity", "genre_count", "is_known_user"]].to_numpy(dtype=np.float32)
        out = deep_model.predict(X, verbose=0)
        return np.asarray(out).reshape(-1)
deep_adapter = Adapter()
users = [u for u in test.userId.unique() if len(test[(test.userId==u)&(test.rating>=4)])>0][:100]
variants = {"popularity": [], "gradient_boosting": [], "deep_ranker": []}
for i,u in enumerate(users):
    relevant = set(test[(test.userId==u)&(test.rating>=4)].movieId.astype(int))
    cands = model.retrieve(int(u), candidate_count=200)
    if not cands: continue
    feats = model._features(int(u), cands)
    # popularity sort
    pop_order = sorted(cands, key=lambda m: model.popularity.get(int(m), model.global_mean), reverse=True)[:10]
    # gradient
    if model.rank_model is not None:
        g_scores = model.rank_model.predict(feats)
    else:
        g_scores = 0.7*feats["popularity_score"].to_numpy() + 0.3*feats["genre_affinity"].to_numpy()
    g_order = [cands[j] for j in np.argsort(g_scores)[::-1][:10]]
    # deep
    d_scores = deep_adapter.predict(feats)
    d_order = [cands[j] for j in np.argsort(d_scores)[::-1][:10]]
    for name, order in [("popularity", pop_order), ("gradient_boosting", g_order), ("deep_ranker", d_order)]:
        variants[name].append((recall_at_k(order, relevant, 10), ndcg_at_k(order, relevant, 10), hit_rate_at_k(order, relevant, 10), precision_at_k(order, relevant, 10)))
    if i % 25 == 0: print("done", i, flush=True)
results = {}
for name, vals in variants.items():
    results[name] = {
        "recall_at_10": round(float(np.mean([v[0] for v in vals])), 6),
        "ndcg_at_10": round(float(np.mean([v[1] for v in vals])), 6),
        "hit_rate_at_10": round(float(np.mean([v[2] for v in vals])), 6),
        "precision_at_10": round(float(np.mean([v[3] for v in vals])), 6),
        "users_evaluated": len(vals)
    }
print(json.dumps(results, indent=2))
payload = {"evaluation_protocol": "same 100 eligible held-out users; chronological test; relevance rating>=4; candidate_count=200; top-10", "ranking_comparison": results}
open("models/ranking_metrics.json", "w").write(json.dumps(payload, indent=2))
