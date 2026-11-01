import os
os.environ.setdefault("TF_USE_LEGACY_KERAS","1")
import numpy as np
import pandas as pd
from src.cf_svd import SvdRetriever
from src.pairwise_ranker import load_pairwise_ranker, score_pairwise_ranker
from src.recommender import TwoStageBaseline
from src.metrics import recall_at_k, ndcg_at_k, hit_rate_at_k, precision_at_k
train=pd.read_csv("data/processed/train.csv")
val=pd.read_csv("data/processed/validation.csv")
movies=pd.read_csv("data/processed/movies.csv")
baseline=TwoStageBaseline().fit(train,movies)
baseline.cf_retriever=SvdRetriever("models/cf_svd")
pairwise=load_pairwise_ranker("models/pairwise_ranker/pairwise_ranker.keras")
retriever=baseline.cf_retriever
eligible=[u for u in val.userId.unique() if ((val.userId==u)&(val.rating>=4)).any()][:100]
seen_map={int(u):set(g.movieId.astype(int)) for u,g in train[train.userId.isin(eligible)].groupby("userId")}
def feat(u,mids):
    f=baseline._features(u,mids)
    cf=[]
    for m in mids:
        if int(u) in retriever.user_to_idx and int(m) in retriever.item_to_idx:
            cf.append(float(retriever.user_factors[retriever.user_to_idx[int(u)]] @ retriever.item_factors[retriever.item_to_idx[int(m)]]))
        else:
            cf.append(0.0)
    f["cf_score"]=cf
    return f[["popularity_score","genre_affinity","genre_count","is_known_user","cf_score"]].to_numpy(dtype=np.float32)
variants={"cf_retrieval":[],"cf_plus_pairwise":[],"cf_plus_popularity":[]}
for u in eligible:
    rel=set(val.loc[(val.userId==u)&(val.rating>=4),"movieId"].astype(int))
    seen=seen_map.get(int(u),set())
    cands=retriever.retrieve(int(u),seen,200)
    if not cands: continue
    X=feat(u,cands)
    scores=score_pairwise_ranker(pairwise,X)
    pw=[cands[i] for i in np.argsort(scores)[::-1][:10]]
    po=sorted(cands,key=lambda m: baseline.popularity.get(int(m),baseline.global_mean),reverse=True)[:10]
    variants["cf_retrieval"].append((recall_at_k(cands,rel,10),ndcg_at_k(cands,rel,10),hit_rate_at_k(cands,rel,10),precision_at_k(cands,rel,10)))
    variants["cf_plus_pairwise"].append((recall_at_k(pw,rel,10),ndcg_at_k(pw,rel,10),hit_rate_at_k(pw,rel,10),precision_at_k(pw,rel,10)))
    variants["cf_plus_popularity"].append((recall_at_k(po,rel,10),ndcg_at_k(po,rel,10),hit_rate_at_k(po,rel,10),precision_at_k(po,rel,10)))
for name,vals in variants.items():
    print(name,{"recall@10":round(float(np.mean([v[0] for v in vals])),6),"ndcg@10":round(float(np.mean([v[1] for v in vals])),6),"hit_rate@10":round(float(np.mean([v[2] for v in vals])),6),"precision@10":round(float(np.mean([v[3] for v in vals])),6),"users":len(vals)})
