import os
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
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
retriever=SvdRetriever("models/cf_svd")
baseline=TwoStageBaseline().fit(train, movies)
deep=load_deep_ranker("models/deep_ranker/deep_ranker.keras")
eligible=[u for u in val.userId.unique() if ((val.userId==u)&(val.rating>=4)).any()][:100]
seen_map={int(u):set(g.movieId.astype(int)) for u,g in train.groupby("userId") if int(u) in set(eligible)}
item_ids=np.array(retriever.item_ids, dtype=int)
item_index={int(m):i for i,m in enumerate(item_ids)}
pop_arr=np.array([baseline.popularity.get(int(m), baseline.global_mean) for m in item_ids], dtype=np.float32)
def metrics_for(order_fn, k_eval):
    R=[];R20=[];N=[];H=[];P=[]
    for u in eligible:
        rel=set(val.loc[(val.userId==u)&(val.rating>=4),"movieId"].astype(int))
        seen=seen_map.get(int(u), set())
        order=order_fn(int(u), seen)
        R.append(recall_at_k(order, rel, 10))
        R20.append(recall_at_k(order, rel, 20))
        N.append(ndcg_at_k(order, rel, 10))
        H.append(hit_rate_at_k(order, rel, 10))
        P.append(precision_at_k(order, rel, 10))
    return {"recall@10":float(np.mean(R)),"recall@20":float(np.mean(R20)),"ndcg@10":float(np.mean(N)),"hit_rate@10":float(np.mean(H)),"precision@10":float(np.mean(P)),"users":len(eligible)}
def cf_order(u, seen):
    if u in retriever.user_to_idx:
        scores=retriever.user_factors[retriever.user_to_idx[u]] @ retriever.item_factors.T
    else:
        scores=pop_arr.copy()
    idx=np.argsort(scores)[::-1]
    out=[]
    for i in idx:
        m=int(item_ids[i])
        if m in seen: continue
        out.append(m)
        if len(out)>=200: break
    return out
def pop_order(u, seen):
    idx=np.argsort(pop_arr)[::-1]
    out=[]
    for i in idx:
        m=int(item_ids[i])
        if m in seen: continue
        out.append(m)
        if len(out)>=200: break
    return out
def deep_order(u, seen):
    cands=[m for m in item_ids if m not in seen][:2000]
    # use all unseen candidates but cap for runtime
    cands=[m for m in item_ids if m not in seen]
    feats=baseline._features(u, cands)
    X=feats[["popularity_score","genre_affinity","genre_count","is_known_user"]].to_numpy(dtype=np.float32)
    scores=deep.predict(X, verbose=0).reshape(-1)
    idx=np.argsort(scores)[::-1]
    return [cands[i] for i in idx[:200]]
print("CF", metrics_for(cf_order, 10))
print("Popularity", metrics_for(pop_order, 10))
print("Deep", metrics_for(deep_order, 10))
