from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any


class Experiment:
    def __init__(self, name: str, variants: list[str], salt: str = "exp"):
        self.name = name
        self.variants = variants
        self.salt = salt
    def assign(self, user_id: int) -> str:
        digest = hashlib.sha256(f"{self.salt}:{self.name}:{user_id}".encode()).hexdigest()
        bucket = int(digest[:8], 16) % len(self.variants)
        return self.variants[bucket]
    def log_assignment(self, path: str | Path, user_id: int, variant: str, metadata: dict[str, Any] | None = None) -> None:
        record = {"experiment": self.name, "user_id": user_id, "variant": variant, "metadata": metadata or {}}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    @staticmethod
    def summarize(log_path: str | Path) -> dict[str, Any]:
        counts = {}
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                counts[rec["variant"]] = counts.get(rec["variant"], 0) + 1
        return {"assignments": counts}


def simulate_ctr(clicks: dict[str, int], impressions: dict[str, int]) -> dict[str, float]:
    """Clearly simulated/derived CTR; not real traffic."""
    out = {}
    for v in impressions:
        out[v] = clicks.get(v, 0) / impressions[v] if impressions[v] else 0.0
    return out
