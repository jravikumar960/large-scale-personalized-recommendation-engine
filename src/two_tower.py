from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

import tensorflow as tf
import tensorflow_recommenders as tfrs
import faiss


class TwoTowerModel(tfrs.Model):
    def __init__(self, user_ids, movie_ids, embedding_dim=32):
        super().__init__()
        self.user_ids = user_ids
        self.movie_ids = movie_ids
        self.user_model = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=user_ids, mask_token=None),
            tf.keras.layers.Embedding(len(user_ids) + 1, embedding_dim),
        ])
        self.item_model = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=movie_ids, mask_token=None),
            tf.keras.layers.Embedding(len(movie_ids) + 1, embedding_dim),
        ])
        self.task = tfrs.tasks.Retrieval()
    def compute_loss(self, features, training=False):
        user_embeddings = tf.nn.l2_normalize(self.user_model(features["user_id"]), axis=1)
        movie_embeddings = tf.nn.l2_normalize(self.item_model(features["movie_id"]), axis=1)
        return self.task(user_embeddings, movie_embeddings)

def build_datasets(train_df, sample_size=200000):
    if len(train_df) > sample_size:
        train_df = train_df.sample(sample_size, random_state=42)
    users = train_df["userId"].astype(str).tolist()
    movies = train_df["movieId"].astype(str).tolist()
    ds = tf.data.Dataset.from_tensor_slices({"user_id": users, "movie_id": movies})
    ds = ds.shuffle(10000).batch(256).cache()
    return ds, train_df

def train_two_tower(train_df, movie_df, output_dir, epochs=1, sample_size=200000):
    user_ids = train_df["userId"].astype(str).unique().tolist()
    movie_ids = movie_df["movieId"].astype(str).unique().tolist()
    model = TwoTowerModel(user_ids, movie_ids)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(0.1))
    ds, _ = build_datasets(train_df, sample_size=sample_size)
    model.fit(ds, epochs=epochs)
    from pathlib import Path
    import json
    import numpy as np
    import faiss
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    model.save_weights(str(out / "two_tower.weights.h5"))
    (out / "movie_ids.json").write_text(json.dumps(movie_ids), encoding="utf-8")
    item_embeddings = model.item_model(tf.constant(movie_ids))
    item_embeddings = tf.nn.l2_normalize(item_embeddings, axis=1).numpy()
    np.save(out / "item_embeddings.npy", item_embeddings)
    index = faiss.IndexFlatIP(item_embeddings.shape[1])
    index.add(item_embeddings.astype("float32"))
    faiss.write_index(index, str(out / "faiss.index"))
    return model, index, movie_ids


class TwoTowerRetriever:
    def __init__(self, artifact_dir):
        import json
        from pathlib import Path
        import numpy as np
        import faiss
        self.artifact_dir = Path(artifact_dir)
        self.movie_ids = json.loads((self.artifact_dir / "movie_ids.json").read_text())
        self.movie_id_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.index = faiss.read_index(str(self.artifact_dir / "faiss.index"))
        cfg = json.loads((self.artifact_dir / "config.json").read_text()) if (self.artifact_dir / "config.json").exists() else {}
        self.user_ids = []
        # Reconstruct user ids from train? Not saved; build from movies only for item side.
        # For user embedding we need model; load weights lazily.
        self.model = None
    def _load_model(self, train_df):
        if self.model is not None:
            return
        import tensorflow as tf
        user_ids = train_df["userId"].astype(str).unique().tolist()
        self.user_ids = user_ids
        self.model = TwoTowerModel(user_ids, self.movie_ids)
        _ = self.model.user_model(tf.constant([user_ids[0]]))
        _ = self.model.item_model(tf.constant([self.movie_ids[0]]))
        self.model.load_weights(str(self.artifact_dir / "two_tower.weights.h5"))
    def retrieve(self, user_id, train_df, k=10):
        self._load_model(train_df)
        import numpy as np
        uid = str(user_id)
        if uid not in self.user_ids:
            return []
        import tensorflow as tf
        user_emb = self.model.user_model(tf.constant([uid]))
        user_emb = tf.nn.l2_normalize(user_emb, axis=1).numpy().astype("float32")
        # Search more to allow filtering seen items.
        seen = set(train_df.loc[train_df.userId.astype(str)==uid, "movieId"].astype(str).tolist()) if train_df is not None else set()
        fetch_k = min(self.index.ntotal, max(k + len(seen), k * 5))
        scores, idx = self.index.search(user_emb, fetch_k)
        out = []
        for i in idx[0]:
            if i < 0: continue
            mid = int(self.movie_ids[i])
            if str(mid) in seen: continue
            out.append(mid)
            if len(out) >= k: break
        return out
