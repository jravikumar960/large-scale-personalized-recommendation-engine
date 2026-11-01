from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)
def test_health():
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
def test_recommendations_unknown_user():
    r = c.get("/recommendations/999999?k=3")
    assert r.status_code == 200
    assert r.json()["count"] >= 0
def test_items_invalid():
    r = c.get("/items/999999999")
    assert r.status_code == 404
def test_metrics():
    r = c.get("/metrics")
    assert r.status_code in (200, 404)
def test_movie_search_title():
    r = c.get("/movies/search?q=toy&limit=5")
    assert r.status_code == 200
    assert r.json()["count"] <= 5
    assert any("Toy Story" in item["title"] for item in r.json()["results"])
def test_movie_search_genre():
    r = c.get("/movies/search?genre=Comedy&limit=5")
    assert r.status_code == 200
    assert r.json()["count"] <= 5
    assert all("Comedy" in item["genres"] for item in r.json()["results"])
def test_movie_search_empty():
    r = c.get("/movies/search?q=zzzzzzzz")
    assert r.status_code == 200
    assert r.json()["count"] == 0
