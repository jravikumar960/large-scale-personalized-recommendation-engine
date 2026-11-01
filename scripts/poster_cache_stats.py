import json
d = json.load(open("models/poster_cache.json", encoding="utf-8"))
print("cached_entries", len(d))
print("verified_posters", sum(v is not None for v in d.values()))
print("examples", list(d.items())[:3])
