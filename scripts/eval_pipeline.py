import json
import numpy as np
import pandas as pd
from src.cf_svd import SvdRetriever
from src.recommender import TwoStageBaseline
from src.deep_ranker import load_deep_ranker
from src.metrics import recall_at_k, ndcg_at_k, hit_rate_at_k, precision_at_k
train=pd.read_csv("data/processed/train.csv")
val=pd.read_csv("data/processed/validation.csv")
movies=pd.read_csv("data/processed/movies.csv")
baseline=TwoStageBaseline().fit(train, movies)
deep=load_deep_ranker("models/deep_ranker/deep_ranker.keras")
retriever=SvdRetriever("models/cf_svd")
eligible=[u for u in val.userId.unique() if ((val.userId==u)&(val.rating>=4)).any()][:100]
seen_map={int(u):set(g.movieId.astype(int)) for u,g in train.groupby("userId") if int(u) in set(eligible)}
def rank_candidates(cands, u, scorer):
    feats=baseline._features(u, cands)
    if scorer=="deep":
        X=feats[["popularity_score","genre_affinity","genre_count","is_known_user"]].to_numpy(dtype=np.float32)
        scores=deep.predict(X, verbose=0).reshape(-1)
    elif scorer=="gradient":
        scores=baseline.rank_model.predict(feats) if baseline.rank_model is not None else 0.7*feats["popularity_score"].to_numpy()+0.3*feats["genre_affinity"].to_numpy()
    else:
        scores=feats["popularity_score"].to_numpy()
    order=[cands[i] for i in np.argsort(scores)[::-1]]
    return order[:10]
variants={"cf_svd_plus_deep":[],"cf_svd_plus_gradient":[],"cf_svd_plus_popularity":[]}
for u in eligible:
    rel=set(val.loc[(val.userId==u)&(val.rating>=4),"movieId"].astype(int))
    cands=retriever.retrieve(int(u), seen_map.get(int(u),set()), 200)
    if not cands: continue
    for name, scorer in [("cf_svd_plus_deep","deep"),("cf_svd_plus_gradient","gradient"),("cf_svd_plus_popularity","popularity")]:
        order=rank_candidates(cands,u,scorer)
        variants[name].append((recall_at_k(order,rel,10),ndcg_at_k(order,rel,10),hit_rate_at_k(order,rel,10),precision_at_k(order,rel,10)))
for name, vals in variants.items():
    print(name, {"recall@10":round(float(np.mean([v[0] for v in vals])),6),"ndcg@10":round(float(np.mean([v[1] for v in vals])),6),"hit_rate@10":round(float(np.mean([v[2] for v in vals])),6),"precision@10":round(float(np.mean([v[3] for v in vals])),6),"users":len(vals)})
