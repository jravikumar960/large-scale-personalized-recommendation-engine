import json
p = "models/poster_cache.json"
cache = json.load(open(p, encoding="utf-8"))
for key in ["89745", "593", "47", "5618"]:
    cache.pop(key, None)
open(p, "w", encoding="utf-8").write(json.dumps(cache))
print("remaining", len(cache), "verified", sum(v is not None for v in cache.values()))
