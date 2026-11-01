Redis caching
Set REDIS_URL, for example redis://localhost:6379/0.
If Redis is unavailable, RecommendationCache falls back to in-memory caching.
In-memory cache entries expire using the configured TTL.
Unit tests use a fake Redis client and do not require a Redis server.
Integration tests require a running Redis server and were not verified locally.
Docker is not installed in the current environment.
