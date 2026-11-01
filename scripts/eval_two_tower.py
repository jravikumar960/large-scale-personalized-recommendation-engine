import pandas as pd
from src.two_tower import TwoTowerRetriever
from src.metrics import recall_at_k
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")
retriever = TwoTowerRetriever("models/two_tower")
users = test["userId"].unique()[:200]
recalls=[]
for u in users:
    relevant = set(test[(test.userId==u)&(test.rating>=4)].movieId.astype(int))
    if not relevant: continue
    try:
        recs = retriever.retrieve(u, train, k=10)
    except Exception as e:
        print("err", u, e); continue
    recalls.append(recall_at_k(recs, relevant, 10))
print("users", len(recalls), "recall@10", sum(recalls)/len(recalls) if recalls else 0)
