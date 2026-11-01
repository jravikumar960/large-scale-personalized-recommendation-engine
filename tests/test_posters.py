import io
import json
from src.posters import _normalize_movie_id, get_poster_url, _wikipedia_poster_url, _is_valid_image_url

def test_normalize_movie_id():
    assert _normalize_movie_id(1) == 1
    assert _normalize_movie_id("2") == 2
    assert _normalize_movie_id("bad") is None

def test_cache_reuse(monkeypatch, tmp_path):
    cache_path = tmp_path / "poster_cache.json"
    monkeypatch.setattr("src.posters.CACHE_PATH", cache_path)
    calls = []
    def fake_wikipedia(title):
        calls.append(title)
        return "https://example.com/poster.jpg"
    monkeypatch.setattr("src.posters._wikipedia_poster_url", fake_wikipedia)
    assert get_poster_url(1, "Movie (2020)") == "https://example.com/poster.jpg"
    assert get_poster_url(1, "Movie (2020)") == "https://example.com/poster.jpg"
    assert len(calls) == 1

def test_invalid_image_returns_none(monkeypatch, tmp_path):
    cache_path = tmp_path / "poster_cache.json"
    monkeypatch.setattr("src.posters.CACHE_PATH", cache_path)
    monkeypatch.setattr("src.posters._wikipedia_poster_url", lambda title: "https://example.com/bad.jpg")
    monkeypatch.setattr("src.posters._is_valid_image_url", lambda url: False)
    monkeypatch.setattr("src.posters._wikipedia_poster_url", lambda title: None)
    assert get_poster_url(2, "Movie (2020)") is None

def test_unavailable_source_returns_none(monkeypatch, tmp_path):
    cache_path = tmp_path / "poster_cache.json"
    monkeypatch.setattr("src.posters.CACHE_PATH", cache_path)
    monkeypatch.setattr("src.posters._wikipedia_poster_url", lambda title: None)
    assert get_poster_url(3, "Movie (2020)") is None

def test_image_validator_rejects_text(monkeypatch):
    class FakeResponse:
        headers = {"Content-Type": "text/html"}
        def read(self, size=-1):
            return b"<html>"
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    import src.posters
    src.posters.urllib.request.urlopen = lambda *args, **kwargs: FakeResponse()
    assert _is_valid_image_url("https://example.com/not-an-image") is False

def test_ambiguous_title_tries_candidates(monkeypatch):
    monkeypatch.setattr("src.posters._is_valid_image_url", lambda url: True)
    calls = []
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload
        def read(self, size=-1):
            return self.payload
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    def fake_urlopen(request, timeout=5):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise Exception("not found")
        return FakeResponse(__import__("json").dumps({"thumbnail": {"source": "https://example.com/poster.jpg"}}).encode("utf-8"))
    import src.posters
    src.posters.urllib.request.urlopen = fake_urlopen
    result = _wikipedia_poster_url("Ambiguous Title (2020)")
    assert result == "https://example.com/poster.jpg"
    assert len(calls) >= 2
