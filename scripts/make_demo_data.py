from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261029)
    genres = ["Action", "Comedy", "Drama", "Sci-Fi", "Romance", "Thriller", "Animation"]
    movies = []
    for mid in range(1, 121):
        selected = rng.choice(genres, size=int(rng.integers(1, 4)), replace=False)
        movies.append({"movieId": mid, "title": f"Demo Movie {mid:03d}", "genres": "|".join(selected)})
    movie_df = pd.DataFrame(movies)
    ratings = []
    base_ts = 1_750_000_000
    for uid in range(1, 81):
        preferred = set(rng.choice(genres, size=2, replace=False))
        chosen = rng.choice(np.arange(1, 121), size=30, replace=False)
        for j, mid in enumerate(chosen):
            mgenres = set(movie_df.loc[movie_df.movieId == mid, "genres"].iloc[0].split("|"))
            score = 3.0 + (0.8 if preferred & mgenres else -0.4) + rng.normal(0, 0.8)
            rating = float(np.clip(round(score * 2) / 2, 0.5, 5.0))
            ratings.append({"userId": uid, "movieId": int(mid), "rating": rating, "timestamp": base_ts + uid * 5000 + j * 3600})
    pd.DataFrame(ratings).sort_values("timestamp").to_csv(OUT / "ratings.csv", index=False)
    movie_df.to_csv(OUT / "movies.csv", index=False)
    print(f"Wrote synthetic smoke-test dataset to {OUT} ({len(ratings)} ratings, {len(movies)} movies).")
    print("Note: this is synthetic data, not suitable for reporting real-world recommendation quality.")

if __name__ == "__main__":
    main()
