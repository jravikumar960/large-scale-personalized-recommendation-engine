from __future__ import annotations
import math


def recall_at_k(recommended, relevant, k):
    if not relevant:
        return 0.0
    return len(set(recommended[:k]) & relevant) / len(relevant)


def hit_rate_at_k(recommended, relevant, k):
    return float(bool(set(recommended[:k]) & relevant))


def ndcg_at_k(recommended, relevant, k):
    dcg = sum(1.0 / math.log2(rank + 2) for rank, item in enumerate(recommended[:k]) if item in relevant)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_hits))
    return dcg / idcg if idcg else 0.0


def precision_at_k(recommended, relevant, k):
    if k <= 0:
        return 0.0
    return len(set(recommended[:k]) & relevant) / k
