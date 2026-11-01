import sys
import time
import types
import json
from src.cache import RecommendationCache

class FakeRedis:
    def __init__(self):
        self.data = {}
    def ping(self):
        return True
    def get(self, key):
        item = self.data.get(key)
        if item is None:
            return None
        value, expires_at = item
        if time.monotonic() > expires_at:
            del self.data[key]
            return None
        return json.dumps(value).encode("utf-8")
    def setex(self, key, ttl, value):
        self.data[key] = (json.loads(value), time.monotonic() + ttl)
    def scan_iter(self, pattern):
        prefix = pattern.replace("*", "")
        return [key for key in list(self.data) if key.startswith(prefix)]
    def delete(self, key):
        self.data.pop(key, None)

def test_in_memory_cache_round_trip():
    cache = RecommendationCache(ttl_seconds=300)
    assert cache.get("missing") is None
    cache.set("key", {"user_id": 1, "items": [10, 20]})
    assert cache.get("key") == {"user_id": 1, "items": [10, 20]}

def test_cache_key_separation():
    cache = RecommendationCache()
    assert cache.make_key(1, 10, "1") != cache.make_key(2, 10, "1")
    assert cache.make_key(1, 10, "1") != cache.make_key(1, 20, "1")
    assert cache.make_key(1, 10, "1") != cache.make_key(1, 10, "2")

def test_in_memory_ttl_expiration():
    cache = RecommendationCache(ttl_seconds=0.01)
    cache.set("key", "value")
    assert cache.get("key") == "value"
    time.sleep(0.02)
    assert cache.get("key") is None

def test_redis_cache_hit_and_miss():
    cache = RecommendationCache(ttl_seconds=300)
    fake = FakeRedis()
    cache._redis = fake
    cache._memory = {}
    assert cache.get("missing") is None
    cache.set("key", {"items": [1, 2]})
    assert fake.data["key"][0] == {"items": [1, 2]}
    assert cache.get("key") == {"items": [1, 2]}

def test_redis_ttl_expiration():
    cache = RecommendationCache(ttl_seconds=0.01)
    fake = FakeRedis()
    cache._redis = fake
    cache._memory = {}
    cache.set("key", "value")
    assert cache.get("key") == "value"
    time.sleep(0.02)
    assert cache.get("key") is None

def test_redis_invalid_data_falls_back():
    class InvalidRedis(FakeRedis):
        def get(self, key):
            return b"not-json"
    cache = RecommendationCache()
    cache._redis = InvalidRedis()
    cache._memory = {}
    assert cache.get("key") is None

def test_redis_unavailable_falls_back(monkeypatch):
    class BadRedis:
        def ping(self):
            raise RuntimeError("connection refused")
    fake_redis = types.ModuleType("redis")
    fake_redis.from_url = lambda url: BadRedis()
    monkeypatch.setitem(sys.modules, "redis", fake_redis)
    cache = RecommendationCache(redis_url="redis://localhost:6379/0")
    assert cache._redis is None

def test_redis_get_failure_falls_back_to_memory():
    class FlakyRedis(FakeRedis):
        def get(self, key):
            raise RuntimeError("boom")
        def setex(self, key, ttl, value):
            raise RuntimeError("boom")
    cache = RecommendationCache()
    cache._redis = FlakyRedis()
    cache._memory = {}
    cache.set("key", "value")
    assert cache.get("key") == "value"

def test_invalidate_version():
    cache = RecommendationCache()
    cache.set("rec:v1:u1:k10", [1])
    cache.set("rec:v2:u1:k10", [2])
    cache.invalidate_version("1")
    assert cache.get("rec:v1:u1:k10") is None
    assert cache.get("rec:v2:u1:k10") == [2]
