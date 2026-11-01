import json
import numpy as np
import pandas as pd
from src.cf_svd import SvdRetriever
from src.recommender import TwoStageBaseline
from src.metrics import recall_at_k, ndcg_at_k, hit_rate_at_k, precision_at_k
train=pd.read_csv("data/processed/train.csv")
val=pd.read_csv("data/processed/validation.csv")
movies=pd.read_csv("data/processed/movies.csv")
retriever=SvdRetriever("models/cf_svd")
baseline=TwoStageBaseline().fit(train, movies)
eligible=[u for u in val.userId.unique() if ((val.userId==u)&(val.rating>=4)).any()][:500]
seen_map={int(u):set(g.movieId.astype(int)) for u,g in train.groupby("userId") if int(u) in set(eligible)}
candidate_items=[int(m) for m in retriever.item_ids]
pop_scores={int(m):baseline.popularity.get(int(m), baseline.global_mean) for m in candidate_items}
def pop_retrieve(user_id,k):
    seen=seen_map.get(int(user_id), set())
    cands=[m for m in candidate_items if m not in seen]
    cands.sort(key=lambda m: pop_scores.get(m, baseline.global_mean), reverse=True)
    return cands[:k]
def metrics_for(rec_fn,k):
    R=[];N=[];H=[];P=[];R20=[]
    for u in eligible:
        rel=set(val.loc[(val.userId==u)&(val.rating>=4),"movieId"].astype(int))
        rec10=rec_fn(int(u),10); rec20=rec_fn(int(u),20)
        R.append(recall_at_k(rec10,rel,10))
        N.append(ndcg_at_k(rec10,rel,10))
        H.append(hit_rate_at_k(rec10,rel,10))
        P.append(precision_at_k(rec10,rel,10))
        R20.append(recall_at_k(rec20,rel,20))
    return {"recall@10":float(np.mean(R)),"recall@20":float(np.mean(R20)),"ndcg@10":float(np.mean(N)),"hit_rate@10":float(np.mean(H)),"precision@10":float(np.mean(P)),"users":len(eligible)}
cf_metrics=metrics_for(lambda u,k: retriever.retrieve(u, seen_map.get(u,set()), k), 10)
pop_metrics=metrics_for(pop_retrieve, 10)
print("CF SVD", cf_metrics)
print("Popularity", pop_metrics)
import json
json.dump({"candidate_set":"cf_svd item vocabulary (40420 items)","relevance":"rating>=4","users":len(eligible),"cf_svd":cf_metrics,"popularity":pop_metrics}, open("models/cf_svd_validation_metrics.json","w"), indent=2)
