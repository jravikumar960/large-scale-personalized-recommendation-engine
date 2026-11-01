# Final Assignment-Compliance Audit

Project root: `C:\Users\jravi\Downloads\recommendation-engine-mvp\recommendation-engine`

Audit date: 2026-10-31  
Source of truth: repository files, existing artifacts, and executed test/build results.

## Commands executed

| Command | Result |
|---|---|
| `& "..\.venv\Scripts\python.exe" -m pytest -q` | **50 passed, 3 warnings** |
| `npm run build` (in `recommendation-engine/web`) | **passed** |
| TensorFlow import check | TensorFlow 2.21.0 available |
| TFRS import check with `TF_USE_LEGACY_KERAS=1` | TFRS 0.7.7 available |
| FAISS import check | FAISS 1.15.1 available |
| PySpark import check | PySpark 4.2.1 available |
| Redis import check | redis 8.1.0 available |
| Airflow import check | Airflow runtime not installed; module is a namespace stub |
| Triton client import check | `ModuleNotFoundError: No module named 'tritonclient'` |
| `Get-Command tritonserver` | not found |

## Requirement audit

| # | Requirement | Status | Evidence | Limitation | Required action before submission |
|---:|---|---|---|---|---|
| 1 | MovieLens 25M dataset and data preparation | Complete | `src/data.py`, `src/prepare_data.py`, `tests/test_data.py` | Raw MovieLens files are external inputs | Ensure raw CSVs are available locally before demo |
| 2 | Temporal train/validation/test split and leakage prevention | Complete | `src/data.py::temporal_split`, `validate_no_leakage`; `tests/test_data.py` | Split depends on timestamp availability | None |
| 3 | Spark preprocessing | Partial / Unit-tested | `src/spark_pipeline.py`; `tests/test_spark_pipeline.py` (2 passed) | Full MovieLens run blocked by Windows Hadoop/Python worker environment | Document limitation; optional retry |
| 4 | TensorFlow Recommenders two-tower retrieval | Partial / Implemented | `src/two_tower.py`; `models/two_tower/*` | Recall@10 = 0.0 on 50 eligible users; no dedicated tests | Keep experimental only; do not promote |
| 5 | FAISS indexing and retrieval | Partial / Implemented | `src/two_tower.py`; `models/two_tower/faiss.index` | No dedicated FAISS tests; retriever requires train DataFrame at runtime | Add or document test coverage |
| 6 | CF SVD baseline and evaluation | Complete | `src/cf_svd.py`; `tests/test_cf_svd.py` (4 passed); `models/cf_svd/*` | Evaluated on sampled validation users | None; production default |
| 7 | Deep ranking and pairwise ranking experiments | Complete | `src/deep_ranker.py`; `src/pairwise_ranker.py`; `tests/test_pairwise_ranker.py` (4 passed) | Ranking does not improve CF SVD Recall@10; pairwise result is marginal | Keep CF SVD as default; document negative result |
| 8 | Cold-start and unknown-user fallback | Complete | `src/cf_svd.py::retrieve`; `src/recommender.py::retrieve`; `tests/test_cf_svd.py`, `tests/test_api.py` | Fallback is popularity-based only | None |
| 9 | Redis caching and fallback behavior | Partial / Unit-tested | `src/cache.py`; `tests/test_cache.py` (9 passed) | Real Redis server not verified locally | Document limitation; optional integration test |
| 10 | Triton model export and serving configuration | Partial / Artifact-verified | `triton/model_repository/deep_ranker/config.pbtxt`; `tests/test_triton_artifact.py` (2 passed) | `tritonserver` and `tritonclient` are not installed | Document limitation; optional installation |
| 11 | Airflow retraining pipeline and safe model promotion | Partial / Structure-tested | `airflow/dags/retraining.py`; `src/airflow_tasks.py`; `tests/test_airflow_tasks.py`, `tests/test_airflow_dag.py` (7 passed) | Airflow runtime is not installed | Document limitation; optional runtime verification |
| 12 | Online A/B testing implementation | Partial / Simulated | `src/ab_testing.py` | Deterministic hashing and simulated CTR only; no live traffic | Label as simulated; do not claim live experimentation |
| 13 | Recall@K, NDCG@K, HitRate, Precision, and CTR | Partial | `src/metrics.py`; `tests/test_metrics.py` | CTR cannot be established without real impression/click data | State explicitly that real CTR is unavailable |
| 14 | Recommendation API and error handling | Complete | `app/main.py`; `tests/test_api.py` (7 passed) | Startup can take about 60 seconds | Verify startup manually before demo |
| 15 | React frontend and responsive UI | Complete / Build-verified | `web/*`; `npm run build` passed | No automated frontend tests; visual responsiveness not programmatically verified | Manual UI review before demo |
| 16 | Automated tests, reproducibility, and latency measurement | Complete / Partial | `pytest -q`: 50 passed, 3 warnings; seeds in scripts; `docs/test_report.md` latency n=20 | Latency measured on one local machine; no CI pipeline | Document measurement conditions |
| 17 | README, architecture, API docs, setup, data dictionary, model card, evaluation report, reflection | Complete | `README.md`, `docs/architecture.md`, `docs/api.md`, `docs/setup_windows.md`, `docs/data_dictionary.md`, `docs/model_card.md`, `docs/evaluation_report.md`, `docs/reflection.md` | Documentation counts were stale before this audit and were corrected | Keep docs synchronized |
| 18 | Demo readiness and presentation requirements | Partial | `docs/presentation_outline.md`; API and frontend build verified | End-to-end demo was not executed in this audit | Run backend + frontend smoke test before presentation |
## Current metrics and sample sizes

### Retrieval (validation)
- CF SVD: Recall@10=0.05095, Recall@20=0.06959, NDCG@10=0.04515, HitRate@10=0.144, Precision@10=0.02420, **500 users**
- Popularity: Recall@10=0.01400, Recall@20=0.02510, NDCG@10=0.02020, HitRate@10=0.098, Precision@10=0.01800, **500 users**

### Ranking (100 eligible held-out users, candidate_count=200)
- Popularity: Recall@10=0.01928, NDCG@10=0.028221, HitRate@10=0.15, Precision@10=0.027
- Gradient boosting: Recall@10=0.010098, NDCG@10=0.015452, HitRate@10=0.07, Precision@10=0.012
- Deep ranker: Recall@10=0.016916, NDCG@10=0.030534, HitRate@10=0.15, Precision@10=0.027

### Validation pairwise experiment (100 eligible validation users, candidate_count=200)
- CF SVD retrieval alone: Recall@10=0.045048, NDCG@10=0.037729, HitRate@10=0.15, Precision@10=0.022
- CF SVD + pairwise ranker: Recall@10=0.046181, NDCG@10=0.037628, HitRate@10=0.16, Precision@10=0.022
- CF SVD + popularity ranking: Recall@10=0.035422, NDCG@10=0.021771, HitRate@10=0.10, Precision@10=0.012

### Baseline test split
- TwoStageBaseline gradient-boosting ranker: Recall@10=0.009757, NDCG@10=0.013401, HitRate@10=0.06682, Precision@10=0.009447, **868 users**

### Two-tower retrieval
- Recall@10=0.0, **50 eligible users**

## CTR statement
Real CTR cannot be established without real impression/click data. The project contains only simulated CTR calculation in `src/ab_testing.py::simulate_ctr`. No live traffic or impression logging exists. Any CTR value must be labeled as simulated.

## A/B testing statement
A/B testing is simulated only. `src/ab_testing.py` provides deterministic assignment hashing and append-only assignment logging, but it is not integrated into the API and does not represent live experimentation.

## Simulated vs. verified distinction
- **Implemented and unit-tested**: data validation, temporal split, CF SVD, metrics, cache fallback, Spark synthetic pipeline, Triton artifact, Airflow task/DAG structure, pairwise ranker.
- **Integration-tested with real services**: none for Redis server, Triton server, Airflow runtime, or Spark full MovieLens run.
- **Manually verified**: SavedModel output comparison to Keras; frontend production build.
- **Simulated**: A/B assignment logging and CTR.
- **Unverified**: full Spark MovieLens run, live Redis, live Triton, live Airflow, live A/B experimentation, real CTR.

## Known limitations
- Spark: full MovieLens preprocessing is blocked by the Windows Hadoop/Python worker environment; only synthetic-data unit tests passed.
- Airflow: DAG structure and task logic are unit-tested with mocked Airflow modules; Airflow runtime is not installed.
- Triton: SavedModel and `config.pbtxt` are verified; `tritonserver` and `tritonclient` are not installed.
- Redis: in-memory fallback and fake-client behavior are tested; no real Redis server was available.
- Two-tower: implemented with TFRS and FAISS and artifacts exist, but retrieval Recall@10 is 0.0 and there are no dedicated tests.
- Ranking: deep and pairwise rankers do not clearly improve CF SVD Recall@10; CF SVD remains the production retrieval default.
- Backend startup can take approximately 60 seconds because of the large serialized model artifact.

## P0: Must fix before submission
1. Run a final backend startup smoke test (`uvicorn app.main:app`) before the demo; startup was not exercised in this audit.
2. Run the frontend against the live backend and verify recommendation rendering manually.
3. Ensure all documentation claims use the current test result: **50 passed, 3 warnings**.
4. Do not describe Spark, Airflow, Triton, Redis, or two-tower as fully verified integrations.

## P1: Important but can be documented as a limitation
1. Spark full MovieLens run remains blocked by environment limitations.
2. Redis real-server integration remains unverified.
3. Triton server inference remains unverified.
4. Airflow runtime remains unverified.
5. Two-tower retrieval remains experimental with zero Recall@10.
6. CTR remains unavailable without real click/impression data.
7. A/B testing remains simulated only.

## P2: Optional improvements
1. Add integration tests for Redis, Triton, Airflow, and FAISS.
2. Add frontend automated tests.
3. Add a reproducible latency benchmark script.
4. Improve ranking features/objectives and re-evaluate with the same protocol.
5. Persist user-side two-tower artifacts and add configuration metadata.

## Low-risk edits made during this audit
- Updated stale test counts from 40 passed / 1 warning to 50 passed / 3 warnings in:
  - `README.md`
  - `docs/implementation_status.md`
  - `docs/test_report.md`
- Aligned `docs/component_audit.md` status wording with `docs/implementation_status.md` for Spark, Triton, and Airflow.
- Created this audit file: `docs/final_compliance_audit.md`.
- No model artifacts, training code, or model-selection behavior were changed.