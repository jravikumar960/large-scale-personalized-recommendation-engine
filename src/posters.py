from __future__ import annotations
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
import pandas as pd

LINKS_PATH = Path("data/raw/movielens/links.csv")
MOVIES_PATH = Path("data/processed/movies.csv")
CACHE_PATH = Path("models/poster_cache.json")


def _normalize_movie_id(movie_id):
    try:
        return int(movie_id)
    except (TypeError, ValueError):
        return None


def _load_links():
    if not LINKS_PATH.exists():
        return {}
    try:
        frame = pd.read_csv(LINKS_PATH)
    except (OSError, ValueError):
        return {}
    result = {}
    for row in frame.itertuples(index=False):
        try:
            movie_id = int(row.movieId)
        except (TypeError, ValueError):
            continue
        tmdb_id = None if pd.isna(row.tmdbId) else int(row.tmdbId)
        result[movie_id] = tmdb_id
    return result


def _load_movies():
    if not MOVIES_PATH.exists():
        return {}
    try:
        frame = pd.read_csv(MOVIES_PATH)
    except (OSError, ValueError):
        return {}
    result = {}
    for row in frame.itertuples(index=False):
        try:
            result[int(row.movieId)] = str(row.title)
        except (TypeError, ValueError):
            continue
    return result


def _load_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass


def _tmdb_poster_url(movie_id, api_key):
    tmdb_id = _load_links().get(movie_id)
    if not tmdb_id:
        return None
    try:
        url = "https://api.themoviedb.org/3/movie/" + str(tmdb_id) + "?api_key=" + api_key
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.load(response)
        poster_path = payload.get("poster_path")
        return "https://image.tmdb.org/t/p/w500" + poster_path if poster_path else None
    except Exception:
        return None


def _normalize_poster_title(title: str | None) -> str:
    if not title:
        return ""
    value = re.sub(r"\s*\(\d{4}\)", "", title).strip()
    value = re.sub(r"\s*\(a\.k\.a\. [^)]*\)", "", value).strip()
    value = re.sub(r", (The|A|An)(\s*\([^)]*\))?$", r" \1\2", value).strip()
    value = re.sub(r"\s*\([^)]*\)", "", value).strip()
    value = re.sub(r", (The|A|An)$", r" \1", value).strip()
    return value


def _is_relevant_poster_result(movie_title: str, payload: dict) -> bool:
    if not payload.get("title") and not payload.get("description") and not payload.get("extract"):
        return True
    page_title = str(payload.get("title") or "")
    description = str(payload.get("description") or "")
    extract = str(payload.get("extract") or "")
    movie_normalized = _normalize_poster_title(movie_title).lower()
    page_normalized = _normalize_poster_title(page_title).lower()
    combined = (description + " " + extract).lower()
    if not movie_normalized or not page_normalized:
        return False
    if page_normalized == movie_normalized:
        if any(term in combined for term in ("film", "movie")):
            return True
        return False
    if movie_normalized in page_normalized or page_normalized in movie_normalized:
        if any(term in combined for term in ("film", "movie", "television series")):
            return True
    return any(term in combined for term in (" film", " movie")) and movie_normalized in page_normalized


def _wikipedia_poster_url(title: str | None) -> str | None:
    if not title:
        return None
    year_match = re.search(r"\((\d{4})\)", title)
    base_title = re.sub(r"\s*\(\d{4}\)", "", title).strip()
    base_title = re.sub(r"\s*\(a\.k\.a\. [^)]*\)", "", base_title).strip()
    base_title = re.sub(r", (The|A|An)(\s*\([^)]*\))?$", r" \1\2", base_title).strip()
    if base_title.endswith(", The"):
        base_title = "The " + base_title[:-5]
    if base_title.endswith(", A"):
        base_title = "A " + base_title[:-3]
    if base_title.endswith(", An"):
        base_title = "An " + base_title[:-4]
    simplified_title = re.sub(r"\s*\([^)]*\)", "", base_title).strip()
    simplified_title = re.sub(r", (The|A|An)$", r" \1", simplified_title).strip()
    candidates = []
    if year_match:
        candidates.append(f"{simplified_title} ({year_match.group(1)} film)")
        candidates.append(f"{base_title} ({year_match.group(1)} film)")
        candidates.append(f"{simplified_title} ({year_match.group(1)})")
        candidates.append(f"{base_title} ({year_match.group(1)})")
    candidates.append(simplified_title)
    candidates.append(base_title)
    candidates.append(title)
    if year_match:
        candidates.append(f"{simplified_title} (film)")
        candidates.append(f"{base_title} (film)")
    unique_candidates = []
    for candidate in candidates:
        if candidate and candidate not in unique_candidates:
            unique_candidates.append(candidate)
    candidates = unique_candidates
    for candidate in candidates:
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(candidate.replace(" ", "_"))
            request = urllib.request.Request(url, headers={"User-Agent": "AIRecommendationEngine/1.0 (academic project)"})
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = json.load(response)
            if not _is_relevant_poster_result(title, payload):
                continue
            thumbnail = payload.get("thumbnail", {}).get("source")
            if thumbnail and _is_valid_image_url(thumbnail):
                return thumbnail
        except Exception:
            continue
    return None

def _is_valid_image_url(url: str) -> bool:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "AIRecommendationEngine/1.0 (academic project)"})
        with urllib.request.urlopen(request, timeout=5) as response:
            content_type = response.headers.get("Content-Type", "")
            if not content_type.lower().startswith("image/"):
                return False
            data = response.read(16)
        return (
            data.startswith(b"\xff\xd8\xff")
            or data.startswith(b"\x89PNG\r\n\x1a\n")
            or data.startswith(b"GIF87a")
            or data.startswith(b"GIF89a")
            or data.startswith(b"RIFF")
        )
    except Exception:
        return False

def get_poster_url(movie_id, title=None):
    normalized_id = _normalize_movie_id(movie_id)
    if normalized_id is None:
        return None
    cache = _load_cache()
    cache_key = str(normalized_id)
    if cache_key in cache:
        return cache[cache_key]
    if title is None:
        title = _load_movies().get(normalized_id)
    api_key = os.getenv("TMDB_API_KEY")
    poster_url = _tmdb_poster_url(normalized_id, api_key) if api_key else None
    if poster_url is None:
        poster_url = _wikipedia_poster_url(title)
    cache[cache_key] = poster_url
    _save_cache(cache)
    return poster_url
