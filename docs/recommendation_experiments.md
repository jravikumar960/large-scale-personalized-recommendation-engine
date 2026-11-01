# Recommendation Experiments

## CF SVD retrieval (production default)
- Dataset: MovieLens 25M chronological train/validation split.
- Candidate universe: CF SVD item vocabulary (40,420 items).
- Validation protocol: 500 validation users; relevance = rating >= 4; top-10.
- Metrics: Recall@10=0.05095, NDCG@10=0.04515.

## Pairwise ranking experiment (isolated, not promoted)
- Objective: test a ranking-specific pairwise (BPR-style) objective instead of pointwise rating regression.
- Training data only: pairs are constructed from `data/processed/train.csv`.
- Positive item: a user's training item with rating >= 4 (maximum 5 positives per user).
- Negative item: a user's training item with rating < 4 when available, otherwise a random item outside that user's positive set.
- Pair count: 100,000 sampled pairs; 80% train / 20% validation split for early stopping.
- Features (5): `popularity_score`, `genre_affinity`, `genre_count`, `is_known_user`, `cf_score`.
- CF score: SVD user-factor/item-factor dot product, or 0.0 for unknown users/items.
- Seed: 42.
- Model: shared MLP (32 -> 16 -> 1) with L2 regularization and dropout; sigmoid difference objective; Adam optimizer; early stopping on validation loss.
- Artifact: `models/pairwise_ranker/pairwise_ranker.keras` with `models/pairwise_ranker/config.json`. Existing production artifacts were not overwritten.
- Validation protocol: 100 eligible validation users; relevance = rating >= 4; candidate generation = CF SVD top-200 after seen-item exclusion.
- Candidate universe: same 40,420-item CF SVD vocabulary.

## Comparison on 100 validation users
| Method | Recall@10 | NDCG@10 | HitRate@10 | Precision@10 |
|---|---:|---:|---:|---:|
| CF SVD retrieval alone (top-200 truncated to 10) | 0.045048 | 0.037729 | 0.15 | 0.022 |
| CF SVD + pairwise ranker | 0.046181 | 0.037628 | 0.16 | 0.022 |
| CF SVD + popularity ranking | 0.035422 | 0.021771 | 0.10 | 0.012 |

## Result
- Pairwise ranking gives a marginal Recall@10 improvement on this 100-user protocol (0.046181 vs 0.045048) but lower NDCG@10 (0.037628 vs 0.037729).
- The difference is small and not sufficient to support replacing CF SVD retrieval.
- CF SVD retrieval remains the production default.
