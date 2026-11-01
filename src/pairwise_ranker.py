from __future__ import annotations
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
import tensorflow as tf


def _feature_vector(recommender, user_id, movie_id):
    base = recommender._features(int(user_id), [int(movie_id)]).iloc[0].to_dict()
    cf_score = 0.0
    if getattr(recommender, "cf_retriever", None) is not None:
        retriever = recommender.cf_retriever
        if int(user_id) in retriever.user_to_idx and int(movie_id) in retriever.item_to_idx:
            cf_score = float(retriever.user_factors[retriever.user_to_idx[int(user_id)]] @ retriever.item_factors[retriever.item_to_idx[int(movie_id)]])
    return np.asarray([base["popularity_score"], base["genre_affinity"], base["genre_count"], base["is_known_user"], cf_score], dtype=np.float32)


def build_pairwise_examples(recommender, train_df, sample_size=100000, seed=42, max_positives_per_user=5):
    rng = np.random.default_rng(seed)
    positive_sets = {int(u): set(g.loc[g.rating >= 4, "movieId"].astype(int)) for u, g in train_df.groupby("userId")}
    all_items = np.asarray(sorted(set(train_df.movieId.astype(int))), dtype=np.int64)
    pairs = []
    for user_id, group in train_df.groupby("userId"):
        positives = group.loc[group.rating >= 4, "movieId"].astype(int).tolist()[:max_positives_per_user]
        negatives = group.loc[group.rating < 4, "movieId"].astype(int).tolist()
        for positive in positives:
            if negatives:
                negative = int(rng.choice(negatives))
            else:
                candidate_negatives = [item for item in all_items if item not in positive_sets[int(user_id)]]
                if not candidate_negatives:
                    continue
                negative = int(rng.choice(candidate_negatives))
            pairs.append((int(user_id), int(positive), int(negative)))
            if len(pairs) >= sample_size:
                break
        if len(pairs) >= sample_size:
            break
    if not pairs:
        raise ValueError("No pairwise training examples could be constructed")
    positive_features = np.asarray([_feature_vector(recommender, u, p) for u, p, _ in pairs], dtype=np.float32)
    negative_features = np.asarray([_feature_vector(recommender, u, n) for u, _, n in pairs], dtype=np.float32)
    return positive_features, negative_features, pairs


def train_pairwise_ranker(recommender, train_df, output_dir, sample_size=100000, seed=42, validation_fraction=0.2, epochs=10, batch_size=1024):
    positive_features, negative_features, pairs = build_pairwise_examples(recommender, train_df, sample_size=sample_size, seed=seed)
    count = len(pairs)
    validation_count = max(1, int(count * validation_fraction))
    train_count = count - validation_count
    Xp_train = positive_features[:train_count]
    Xn_train = negative_features[:train_count]
    Xp_val = positive_features[train_count:]
    Xn_val = negative_features[train_count:]
    y_train = np.ones(train_count, dtype=np.float32)
    y_val = np.ones(validation_count, dtype=np.float32)
    positive_input = tf.keras.layers.Input(shape=(5,), name="positive_features")
    negative_input = tf.keras.layers.Input(shape=(5,), name="negative_features")
    shared = tf.keras.Sequential([
        tf.keras.layers.Dense(32, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(1e-4)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(16, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(1e-4)),
        tf.keras.layers.Dense(1),
    ])
    positive_score = shared(positive_input)
    negative_score = shared(negative_input)
    difference = tf.keras.layers.Subtract()([positive_score, negative_score])
    probability = tf.keras.layers.Activation("sigmoid")(difference)
    model = tf.keras.Model([positive_input, negative_input], probability)
    scorer = tf.keras.Model(positive_input, positive_score)
    model.compile(optimizer=tf.keras.optimizers.Adam(0.001), loss="binary_crossentropy")
    early_stopping = tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=2, restore_best_weights=True)
    history = model.fit([Xp_train, Xn_train], y_train, validation_data=([Xp_val, Xn_val], y_val), epochs=epochs, batch_size=batch_size, callbacks=[early_stopping], verbose=1)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    scorer.save(output / "pairwise_ranker.keras")
    (output / "config.json").write_text(json.dumps({"features": ["popularity_score", "genre_affinity", "genre_count", "is_known_user", "cf_score"], "sample_size": len(pairs), "train_pairs": train_count, "validation_pairs": validation_count, "seed": seed, "epochs_requested": epochs, "epochs_completed": len(history.history["loss"]), "early_stopping": True}, indent=2), encoding="utf-8")
    return scorer, history


def load_pairwise_ranker(path):
    return tf.keras.models.load_model(path)


def score_pairwise_ranker(model, features):
    return model.predict(features, verbose=0).reshape(-1)
