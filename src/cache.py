from __future__ import annotations
import json
import os
import time
from typing import Any, Optional


class RecommendationCache:
    """Optional Redis cache with in-memory fallback."""
    def __init__(self, redis_url: str | None = None, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._redis = None
        self._memory = {}
        self._memory_ttl = ttl_seconds
        url = redis_url or os.getenv("REDIS_URL")
        if url:
            try:
                import redis
                self._redis = redis.from_url(url)
                self._redis.ping()
            except Exception:
                self._redis = None
    def make_key(self, user_id: int, k: int, model_version: str) -> str:
        return f"rec:v{model_version}:u{user_id}:k{k}"
    def get(self, key: str) -> Optional[Any]:
        if self._redis is not None:
            try:
                raw = self._redis.get(key)
                if raw is not None:
                    return json.loads(raw)
            except Exception:
                pass
        value, expires_at = self._memory.get(key, (None, 0.0))
        if expires_at and time.monotonic() > expires_at:
            self._memory.pop(key, None)
            return None
        return value
    def set(self, key: str, value: Any) -> None:
        if self._redis is not None:
            try:
                self._redis.setex(key, self.ttl, json.dumps(value))
                return
            except Exception:
                pass
        self._memory[key] = (value, time.monotonic() + self.ttl)
    def invalidate_version(self, model_version: str) -> None:
        if self._redis is not None:
            try:
                for key in self._redis.scan_iter(f"rec:v{model_version}:*"):
                    self._redis.delete(key)
            except Exception:
                pass
        self._memory = {k: v for k, v in self._memory.items() if f"v{model_version}" not in k}
