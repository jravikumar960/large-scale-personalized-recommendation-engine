import os
os.environ.setdefault("TF_USE_LEGACY_KERAS","1")
import numpy as np
import pandas as pd
import tensorflow as tf
import tensorflow_recommenders as tfrs
train=pd.read_csv("data/processed/train.csv").sample(20000, random_state=42)
test=pd.read_csv("data/processed/test.csv")
movies=pd.read_csv("data/processed/movies.csv")
user_ids=train.userId.astype(str).unique().tolist()
movie_ids=movies.movieId.astype(str).unique().tolist()
candidates=tf.data.Dataset.from_tensor_slices(movie_ids).batch(128)
class M(tfrs.Model):
    def __init__(self):
        super().__init__()
        self.u=tf.keras.Sequential([tf.keras.layers.StringLookup(vocabulary=user_ids,mask_token=None),tf.keras.layers.Embedding(len(user_ids)+1,32)])
        self.i=tf.keras.Sequential([tf.keras.layers.StringLookup(vocabulary=movie_ids,mask_token=None),tf.keras.layers.Embedding(len(movie_ids)+1,32)])
        self.task=tfrs.tasks.Retrieval(metrics=tfrs.metrics.FactorizedTopK(candidates=candidates.map(self.i)),num_hard_negatives=5)
    def compute_loss(self,f,training=False):
        return self.task(tf.nn.l2_normalize(self.u(f["user_id"]),axis=1), tf.nn.l2_normalize(self.i(f["movie_id"]),axis=1))
m=M(); m.compile(optimizer=tf.keras.optimizers.Adagrad(0.05))
ds=tf.data.Dataset.from_tensor_slices({"user_id":train.userId.astype(str).tolist(),"movie_id":train.movieId.astype(str).tolist()}).shuffle(10000).batch(256)
m.fit(ds,epochs=1,verbose=0)
item_emb=tf.nn.l2_normalize(m.i(tf.constant(movie_ids)),axis=1).numpy().astype("float32")
eligible=[u for u in test.userId.unique() if ((test.userId==u)&(test.rating>=4)).any()][:50]
rec10=[]; rec50=[]
for u in eligible:
    rel=set(test.loc[(test.userId==u)&(test.rating>=4),"movieId"].astype(int))
    if str(u) not in user_ids: rec10.append(0.0); rec50.append(0.0); continue
    ue=tf.nn.l2_normalize(m.u(tf.constant([str(u)])),axis=1).numpy().astype("float32")
    scores=item_emb @ ue[0]
    seen=set(train.loc[train.userId==u,"movieId"].astype(int))
    order=np.argsort(scores)[::-1]
    rec=[]
    for i in order:
        mid=int(movie_ids[i])
        if mid in seen: continue
        rec.append(mid)
        if len(rec)>=50: break
    rec10.append(len(set(rec[:10])&rel)/max(1,len(rel)))
    rec50.append(len(set(rec[:50])&rel)/max(1,len(rel)))
print("users", len(eligible), "Recall@10", np.mean(rec10), "Recall@50", np.mean(rec50))
