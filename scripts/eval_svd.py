import json
import numpy as np
import pandas as pd
train=pd.read_csv("data/processed/train.csv")
test=pd.read_csv("data/processed/test.csv")
U=np.load("models/_svd_U.npy")
s=np.load("models/_svd_s.npy")
Vt=np.load("models/_svd_Vt.npy")
users=json.load(open("models/_svd_users.json"))
items=json.load(open("models/_svd_items.json"))
uid={u:i for i,u in enumerate(users)}
iid={m:i for i,m in enumerate(items)}
UF=U*s
IF=Vt.T
eligible=[u for u in test.userId.unique() if ((test.userId==u)&(test.rating>=4)).any()]
def metrics(k):
    R=[]
    for u in eligible[:200]:
        rel=set(test.loc[(test.userId==u)&(test.rating>=4),"movieId"].astype(int))
        if u not in uid: continue
        seen=set(train.loc[train.userId==u,"movieId"].astype(int))
        scores=UF[uid[u]] @ IF.T
        order=np.argsort(scores)[::-1]
        rec=[]
        for i in order:
            mid=items[i]
            if mid in seen: continue
            rec.append(mid)
            if len(rec)>=k: break
        R.append(len(set(rec)&rel)/max(1,len(rel)))
    return np.mean(R), len(R)
for k in [10,20,50]:
    print("Recall@",k,metrics(k))
