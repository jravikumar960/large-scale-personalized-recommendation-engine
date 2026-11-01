from __future__ import annotations
import logging
from collections import defaultdict
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


logger = logging.getLogger(__name__)


class TwoStageBaseline:
    def __init__(self) -> None:
        self.movies = pd.DataFrame()
        self.popularity = {}
        self.user_seen = defaultdict(set)
        self.user_genre_scores = {}
        self.genre_map = {}
        self.rank_model = None
        self.global_mean = 3.5
    @staticmethod
    def _genres(value):
        if not isinstance(value, str) or value in ("", "(no genres listed)"):
            return set()
        return set(value.split("|"))

    def fit(self, train, movies):
        self.movies = movies.copy().reset_index(drop=True)
        self.genre_map = {int(r.movieId): self._genres(r.genres) for r in self.movies.itertuples(index=False)}
        self.global_mean = float(train["rating"].mean()) if len(train) else 3.5
        agg = train.groupby("movieId")["rating"].agg(["mean", "count"]) if len(train) else pd.DataFrame()
        prior, strength = self.global_mean, 10.0
        self.popularity = {}
        for movie_id, row in agg.iterrows():
            self.popularity[int(movie_id)] = float((row["count"] * row["mean"] + strength * prior) / (row["count"] + strength))
        seen_map = train.groupby("userId")["movieId"].agg(lambda s: set(int(x) for x in s))
        self.user_seen = defaultdict(set, {int(u): v for u, v in seen_map.items()})
        liked = train[train["rating"] >= 3.5]
        user_genres = defaultdict(lambda: defaultdict(list))
        for r in liked.itertuples(index=False):
            for g in self.genre_map.get(int(r.movieId), set()):
                user_genres[int(r.userId)][g].append(float(r.rating))
        self.user_genre_scores = {uid: {g: float(np.mean(scores)) for g, scores in gd.items()} for uid, gd in user_genres.items()}
        return self

    def retrieve(self, user_id, candidate_count=200):
        seen = self.user_seen.get(int(user_id), set())
        if getattr(self, "cf_retriever", None) is not None:
            try:
                candidates = self.cf_retriever.retrieve(int(user_id), seen, k=candidate_count)
                if candidates:
                    return candidates
                logger.warning("CF SVD returned no candidates for user %s; using baseline retrieval", user_id)
            except Exception:
                logger.exception("CF SVD retrieval failed for user %s; using baseline retrieval", user_id)
        genre_scores = self.user_genre_scores.get(int(user_id), {})
        movie_ids = self.movies["movieId"].astype(int).tolist()
        scored = []
        for movie_id in movie_ids:
            if movie_id in seen:
                continue
            genres = self.genre_map.get(movie_id, set())
            if genre_scores and genres:
                matches = [genre_scores[g] for g in genres if g in genre_scores]
                affinity = float(np.mean(matches)) if matches else 0.0
            else:
                affinity = 0.0
            pop = self.popularity.get(movie_id, self.global_mean)
            score = 0.75 * pop + 0.25 * (affinity if affinity else self.global_mean)
            scored.append((score, movie_id))
        scored.sort(reverse=True)
        return [mid for _, mid in scored[:max(1, candidate_count)]]


    def _features(self, user_id, movie_ids):
        genre_scores = self.user_genre_scores.get(int(user_id), {})
        rows = []
        for movie_id in movie_ids:
            genres = self.genre_map.get(int(movie_id), set())
            matches = [genre_scores[g] for g in genres if g in genre_scores]
            genre_affinity = float(np.mean(matches)) if matches else self.global_mean
            rows.append({
                "popularity_score": self.popularity.get(int(movie_id), self.global_mean),
                "genre_affinity": genre_affinity,
                "genre_count": len(genres),
                "is_known_user": int(int(user_id) in self.user_seen),
            })
        return pd.DataFrame(rows, columns=["popularity_score", "genre_affinity", "genre_count", "is_known_user"])


    def train_ranker(self, train):
        features, labels = [], []
        for row in train.itertuples(index=False):
            mid, uid = int(row.movieId), int(row.userId)
            f = self._features(uid, [mid]).iloc[0].to_dict()
            features.append(f)
            labels.append(float(row.rating))
        if len(features) < 10:
            return
        self.rank_model = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.08, max_leaf_nodes=15, random_state=42)
        self.rank_model.fit(pd.DataFrame(features), np.asarray(labels))


    def recommend(self, user_id, k=10, candidate_count=200):
        if k < 1 or k > 100:
            raise ValueError("k must be between 1 and 100")
        candidates = self.retrieve(user_id, candidate_count=max(candidate_count, k))
        if not candidates:
            return []
        feats = self._features(user_id, candidates)
        if getattr(self, "deep_rank_model", None) is not None:
            scores = self.deep_rank_model.predict(feats)
        elif self.rank_model is not None:
            scores = self.rank_model.predict(feats)
        else:
            scores = 0.7 * feats["popularity_score"].to_numpy() + 0.3 * feats["genre_affinity"].to_numpy()
        score_map = dict(zip(candidates, scores))
        top_ids = sorted(candidates, key=lambda mid: score_map[mid], reverse=True)[:k]
        metadata = self.movies.set_index("movieId").to_dict("index")
        return [{
            "movie_id": int(mid),
            "title": str(metadata.get(mid, {}).get("title", f"Movie {mid}")),
            "genres": str(metadata.get(mid, {}).get("genres", "")),
            "score": round(float(score_map[mid]), 4),
        } for mid in top_ids]

    def save(self, path):
        joblib.dump(self, path)

    @classmethod
    def load(cls, path):
        model = joblib.load(path)
        if not isinstance(model, cls):
            raise TypeError("Saved artifact is not a TwoStageBaseline")
        return model
