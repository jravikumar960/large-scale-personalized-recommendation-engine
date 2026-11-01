from __future__ import annotations
import numpy as np
import pandas as pd
from collections import defaultdict


class PopularityRecommender:
    def __init__(self):
        self.movies = pd.DataFrame()
        self.popularity = {}
        self.global_mean = 3.5
        self.user_seen = defaultdict(set)
    def fit(self, train, movies):
        self.movies = movies.copy().reset_index(drop=True)
        self.global_mean = float(train["rating"].mean()) if len(train) else 3.5
        agg = train.groupby("movieId")["rating"].agg(["mean", "count"]) if len(train) else pd.DataFrame()
        prior, strength = self.global_mean, 10.0
        self.popularity = {}
        for movie_id, row in agg.iterrows():
            self.popularity[int(movie_id)] = float((row["count"] * row["mean"] + strength * prior) / (row["count"] + strength))
        for row in train.itertuples(index=False):
            self.user_seen[int(row.userId)].add(int(row.movieId))
        return self
    def recommend(self, user_id, k=10):
        seen = self.user_seen.get(int(user_id), set())
        candidates = [mid for mid in self.movies["movieId"].astype(int).tolist() if mid not in seen]
        candidates.sort(key=lambda m: self.popularity.get(m, self.global_mean), reverse=True)
        metadata = self.movies.set_index("movieId").to_dict("index")
        out = []
        for mid in candidates[:k]:
            out.append({"movie_id": int(mid), "title": str(metadata.get(mid, {}).get("title", f"Movie {mid}")), "genres": str(metadata.get(mid, {}).get("genres", "")), "score": round(float(self.popularity.get(mid, self.global_mean)), 4)})
        return out
