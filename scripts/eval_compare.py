import pandas as pd
from src.recommender import TwoStageBaseline
from src.two_tower import TwoTowerRetriever
from src.metrics import recall_at_k, ndcg_at_k, hit_rate_at_k, precision_at_k
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")
model = TwoStageBaseline.load("models/recommender.joblib")
retriever = TwoTowerRetriever("models/two_tower")
users = [u for u in test.userId.unique() if len(test[(test.userId==u)&(test.rating>=4)])>0][:50]
def eval_recs(rec_fn, name):
    R,N,H,P=[],[],[],[]
    for i,u in enumerate(users):
        rel = set(test[(test.userId==u)&(test.rating>=4)].movieId.astype(int))
        recs = rec_fn(u)
        R.append(recall_at_k(recs,rel,10)); N.append(ndcg_at_k(recs,rel,10)); H.append(hit_rate_at_k(recs,rel,10)); P.append(precision_at_k(recs,rel,10))
        if i%10==0: print(name, i, flush=True)
    return sum(R)/len(R), sum(N)/len(N), sum(H)/len(H), sum(P)/len(P)
br = eval_recs(lambda u: [x["movie_id"] for x in model.recommend(u,k=10)], "baseline")
tr = eval_recs(lambda u: retriever.retrieve(u, train, k=10), "two_tower")
print("users", len(users))
print("baseline", br)
print("two_tower", tr)
