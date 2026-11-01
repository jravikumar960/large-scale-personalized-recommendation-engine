from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

import os
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
import tensorflow as tf


def build_features(train_df, recommender):
    # returns X (numpy), y
    X = []
    y = []
    for row in train_df.itertuples(index=False):
        feats = recommender._features(int(row.userId), [int(row.movieId)]).iloc[0].to_dict()
        X.append([feats["popularity_score"], feats["genre_affinity"], feats["genre_count"], feats["is_known_user"]])
        y.append(float(row.rating))
    return np.asarray(X, dtype=np.float32), np.asarray(y, dtype=np.float32)


def train_deep_ranker(train_df, recommender, output_dir, epochs=3, sample_size=100000):
    if len(train_df) > sample_size:
        train_df = train_df.sample(sample_size, random_state=42)
    X, y = build_features(train_df, recommender)
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(4,)),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(1),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(0.001), loss="mse")
    model.fit(X, y, epochs=epochs, batch_size=256, verbose=1)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    model.save(out / "deep_ranker.keras")
    return model


def load_deep_ranker(path):
    return tf.keras.models.load_model(path)
