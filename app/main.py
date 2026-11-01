from __future__ import annotations
import os
import threading
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.recommender import TwoStageBaseline
from src.cache import RecommendationCache
from src.cf_svd import SvdRetriever
from src.posters import get_poster_url

MODEL_PATH = Path(os.getenv("RECOMMENDER_MODEL_PATH", "models/recommender.joblib"))
METRICS_PATH = Path(os.getenv("RECOMMENDER_METRICS_PATH", "models/metrics.json"))
DEEP_RANKER_PATH = Path(os.getenv("DEEP_RANKER_PATH", "models/deep_ranker/deep_ranker.keras"))
CF_SVD_PATH = Path(os.getenv("CF_SVD_PATH", "models/cf_svd"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "1")

app = FastAPI(title="Personalized Recommendation Engine", version="0.2.1", description="Two-stage movie recommendation API")
@app.on_event("startup")
def _startup():
    get_model()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
_model = None
_cf_retriever = None
_cf_error = None
_cf_attempted = False
_cache = RecommendationCache(ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")))


def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Model not found. Run python -m src.train first.")
        _model = TwoStageBaseline.load(MODEL_PATH)
        _model.deep_rank_model = None
        global _cf_retriever, _cf_error, _cf_attempted
        if not _cf_attempted:
            _cf_attempted = True
            try:
                if CF_SVD_PATH.exists():
                    _cf_retriever = SvdRetriever(CF_SVD_PATH)
                    _model.cf_retriever = _cf_retriever
                else:
                    _cf_error = f"CF SVD artifacts not found: {CF_SVD_PATH}"
            except Exception as exc:
                _cf_error = f"{type(exc).__name__}: {exc}"
                import logging
                logging.getLogger(__name__).exception("Failed to load CF SVD artifacts from %s", CF_SVD_PATH)

        def load_deep_ranker_in_background(model):
            try:
                if DEEP_RANKER_PATH.exists():
                    import numpy as np
                    from src.deep_ranker import load_deep_ranker
                    keras_model = load_deep_ranker(DEEP_RANKER_PATH)
                    class _Adapter:
                        def __init__(self, m): self.m = m
                        def predict(self, feats):
                            X = feats[["popularity_score", "genre_affinity", "genre_count", "is_known_user"]].to_numpy(dtype=np.float32)
                            out = self.m.predict(X, verbose=0)
                            return np.asarray(out).reshape(-1)
                    model.deep_rank_model = _Adapter(keras_model)
            except Exception as exc:
                model.deep_rank_model = None
                import logging
                logging.getLogger(__name__).warning("Deep ranker unavailable: %s", exc)

        threading.Thread(target=load_deep_ranker_in_background, args=(_model,), daemon=True).start()
    return _model


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _model is not None, "deep_ranker_loaded": bool(getattr(_model, "deep_rank_model", None)), "cf_svd_loaded": _cf_retriever is not None, "cf_svd_error": _cf_error, "model_path": str(MODEL_PATH), "model_version": MODEL_VERSION}


@app.get("/recommendations/{user_id}")
def recommendations(user_id: int, k: int = Query(default=10, ge=1, le=100)):
    model = get_model()
    key = _cache.make_key(user_id, k, MODEL_VERSION)
    cached = _cache.get(key)
    if cached is not None:
        return {"user_id": user_id, "count": len(cached), "recommendations": cached, "cached": True}
    results = model.recommend(user_id=user_id, k=k)
    for result in results:
        result["poster_url"] = get_poster_url(result["movie_id"], result.get("title"))
    _cache.set(key, results)
    return {"user_id": user_id, "count": len(results), "recommendations": results, "cached": False}


@app.get("/items/{item_id}")
def item_details(item_id: int):
    model = get_model()
    found = model.movies[model.movies["movieId"].astype(int) == item_id]
    if found.empty:
        raise HTTPException(status_code=404, detail="Item not found")
    row = found.iloc[0]
    return {"item_id": int(row["movieId"]), "title": str(row["title"]), "genres": str(row["genres"]), "poster_url": get_poster_url(int(row["movieId"]), str(row["title"]))}


@app.get("/movies/search")
def search_movies(q: str = Query(default="", max_length=100), genre: str | None = Query(default=None), limit: int = Query(default=20, ge=1, le=100)):
    model = get_model()
    frame = model.movies.copy()
    if q.strip():
        frame = frame[frame["title"].astype(str).str.contains(q.strip(), case=False, regex=False, na=False)]
    if genre:
        frame = frame[frame["genres"].astype(str).str.split("|").apply(lambda values: genre in values)]
    frame = frame.head(limit)
    return {"query": q, "genre": genre, "count": len(frame), "results": [{"movie_id": int(row["movieId"]), "title": str(row["title"]), "genres": str(row["genres"]), "poster_url": get_poster_url(int(row["movieId"]), str(row["title"]))} for _, row in frame.iterrows()]}

@app.get("/movies/{movie_id}")
def movie_details(movie_id: int):
    return item_details(movie_id)


@app.get("/metrics")
def metrics():
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="Metrics not found. Run training first.")
    import json
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
