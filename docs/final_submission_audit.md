# Final Submission Audit

Project: Large-Scale Personalized Recommendation Engine (AIML-03)  
Project path: `C:\Users\jravi\Downloads\recommendation-engine-mvp\recommendation-engine`  
Audit date: 2026-10-31  
Submission deadline: November 20, 2026

This audit is based on repository files, saved artifacts, documentation, and executed verification commands. It does not infer successful execution from file existence alone.

## 1. Verification commands and results

| Command | Result |
|---|---|
| `& "..\.venv\Scripts\python.exe" -m pytest -q` | **50 passed, 3 warnings** |
| `npm run build` (in `web`) | **passed** |
| `GET /health` during live smoke test | **200 OK**; model, CF SVD, and deep ranker loaded |
| `GET /recommendations/1?k=10` | **200 OK**; 10 recommendations with expected fields |
| `GET /recommendations/999999?k=3` | **200 OK**; unknown-user fallback returned 3 recommendations |
| `GET /movies/search?q=toy&limit=5` | **200 OK** |
| `GET /metrics` | **200 OK** |
| `GET /docs` | **200 OK** |
| CORS preflight from frontend origin | **200 OK** |
| `pytest tests/test_posters.py -q` | **6 passed** |
| Python imports: TensorFlow, TFRS, FAISS, PySpark, Redis | Available |
| Python import: Airflow | Not installed; namespace stub only |
| Python import: Triton client / `tritonserver` | Not installed / not found |

## 2. Requirement checklist

| # | Requirement | Classification | Evidence | Limitation / required action |
|---:|---|---|---|---|
| 1 | MovieLens 25M dataset and data preprocessing | Implemented and verified | `src/data.py`, `src/prepare_data.py`, `tests/test_data.py` | Raw MovieLens files are external inputs; ensure they are available before demo |
| 2 | Chronological train/validation/test split | Implemented and verified | `src/data.py::temporal_split`, `validate_no_leakage`; `tests/test_data.py` | Depends on timestamps |
| 3 | Spark preprocessing pipeline | Implemented but only partially verified | `src/spark_pipeline.py`; `tests/test_spark_pipeline.py` (2 passed) | Full MovieLens run blocked by Windows Hadoop/Python worker environment; only synthetic data verified |
| 4 | TFRS two-tower retrieval and FAISS indexing | Implemented but only partially verified | `src/two_tower.py`; `models/two_tower/*` | Recall@10 = 0.0 on 50 eligible users; no dedicated tests; user-side model is not persisted |
| 5 | Deep ranking model | Implemented and verified | `src/deep_ranker.py`; `tests/test_triton_artifact.py` (SavedModel comparison); `models/deep_ranker/*` | Does not improve CF SVD Recall@10; remains experimental ranking support |
| 6 | Cold-start recommendation fallback | Implemented and verified | `src/cf_svd.py::retrieve`, `src/recommender.py::retrieve`; `tests/test_cf_svd.py`, `tests/test_api.py` | Popularity-based fallback only |
| 7 | Redis caching and fallback behavior | Implemented but only partially verified | `src/cache.py`; `tests/test_cache.py` (9 passed) | Real Redis server not verified locally; in-memory fallback tested with fake client |
| 8 | Triton model-serving configuration | Implemented but only partially verified | `triton/model_repository/deep_ranker/config.pbtxt`; `tests/test_triton_artifact.py` (2 passed) | `tritonserver` and `tritonclient` are not installed; server inference not verified |
| 9 | Airflow retraining workflow | Implemented but only partially verified | `airflow/dags/retraining.py`; `src/airflow_tasks.py`; `tests/test_airflow_tasks.py`, `tests/test_airflow_dag.py` (7 passed) | Airflow runtime is not installed; DAG structure is tested with mocked modules |
| 10 | Recommendation evaluation: Recall@K, NDCG@K, HitRate, Precision | Implemented and verified | `src/metrics.py`; `tests/test_metrics.py`; `models/metrics.json`; `models/cf_svd_validation_metrics.json` | Metrics are from sampled validation users; protocols must not be mixed |
| 11 | Online A/B testing implementation | Simulated only | `src/ab_testing.py` | Deterministic assignment and simulated CTR only; no live traffic or API integration |
| 12 | API functionality and frontend integration | Implemented and verified | `app/main.py`; `tests/test_api.py` (7 passed); live smoke test | Backend startup takes about 60-90 seconds |
| 13 | Automated tests | Implemented and verified | `pytest -q`: 50 passed, 3 warnings; frontend `npm run build`: passed | No frontend automated tests |
| 14 | Performance measurements | Partially verified | `scripts/latency.py`; `scripts/time_model_load.py`; `docs/test_report.md` | Latency measured on one local machine with 20 sequential requests; no CI benchmark |
| 15 | README, architecture, evaluation report, model card, reflection | Implemented and verified | `README.md`, `docs/architecture.md`, `docs/api.md`, `docs/setup_windows.md`, `docs/data_dictionary.md`, `docs/model_card.md`, `docs/evaluation_report.md`, `docs/reflection.md` | Documentation was updated during audits; keep synchronized with code and metrics |## 3. Verified recommendation metrics

### Primary retrieval: CF SVD (500 validation users)
- Recall@10: `0.05095`
- Recall@20: `0.06959`
- NDCG@10: `0.04515`
- HitRate@10: `0.144`
- Precision@10: `0.02420`

### Popularity baseline (same 500 validation users)
- Recall@10: `0.01400`
- Recall@20: `0.02510`
- NDCG@10: `0.02020`
- HitRate@10: `0.098`
- Precision@10: `0.01800`

### Ranking comparison (100 eligible held-out users, candidate_count=200)
- Popularity: Recall@10 `0.01928`, NDCG@10 `0.028221`, HitRate@10 `0.15`, Precision@10 `0.027`
- Gradient boosting: Recall@10 `0.010098`, NDCG@10 `0.015452`, HitRate@10 `0.07`, Precision@10 `0.012`
- Deep ranker: Recall@10 `0.016916`, NDCG@10 `0.030534`, HitRate@10 `0.15`, Precision@10 `0.027`

### End-to-end retrieval + ranking (100 eligible validation users, CF SVD top-200 candidates)
- CF SVD retrieval alone: Recall@10 `0.045048`, Recall@20 `0.063759`, NDCG@10 `0.038580`, HitRate@10 `0.16`, Precision@10 `0.023`
- CF SVD + deep ranker: Recall@10 `0.009078`, Recall@20 `0.009348`, NDCG@10 `0.010772`, HitRate@10 `0.05`, Precision@10 `0.005`
- CF SVD + popularity ranking: Recall@10 `0.015861`, Recall@20 `0.022977`, NDCG@10 `0.015345`, HitRate@10 `0.07`, Precision@10 `0.010`

### Two-tower retrieval
- Recall@10: `0.0` on 50 eligible users

### Important metric notes
- CF SVD is the primary retrieval model and the only retrieval method with a measured improvement over popularity.
- Deep ranker and popularity reranking do not improve CF SVD Recall@10.
- Pairwise ranking is a separate experiment and did not improve CF SVD Recall@10.
- The 500-user, 100-user, and 50-user results use different protocols and sample sizes and must not be combined into one claim.
- CTR cannot be established without real impression/click data. Simulated CTR only exists in `src/ab_testing.py`.
- A/B testing is simulated only; it is not integrated into the API and does not represent live experimentation.

## 4. Security and repository checks

- No hardcoded API keys or credentials were found in application code.
- `TMDB_API_KEY` is read from the environment only.
- `.gitignore` ignores `.env`, raw datasets, processed CSVs, and common Python cache files.
- `.gitignore` was updated to also ignore recursive model artifacts (`.json`, `.npy`, `.keras`, `.h5`, `.joblib`, `.weights.h5`).
- No git repository metadata was present in the project directory, so version-control status could not be verified.

## 5. Instructions for running from a clean environment

Backend:
```powershell
cd recommendation-engine
& "..\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& "..\.venv\Scripts\python.exe" scripts\make_demo_data.py
& "..\.venv\Scripts\python.exe" -m src.prepare_data --input-dir data\raw\movielens --output-dir data\processed --test-days 30 --validation-days 7
& "..\.venv\Scripts\python.exe" -m src.train --data-dir data\processed --model-dir models
& "..\.venv\Scripts\python.exe" -m src.train_cf_svd --data-dir data\processed --output-dir models\cf_svd --k 38
& "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:
```powershell
cd recommendation-engine\web
npm install
npm run dev
```

URLs:
- API: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- Frontend: `http://localhost:5173`

Tests:
```powershell
& "..\.venv\Scripts\python.exe" -m pytest -q
cd web
npm run build
```

## 6. Remaining blockers and limitations

- Spark full MovieLens preprocessing is blocked by the Windows Hadoop/Python worker environment; only synthetic-data tests passed.
- Airflow runtime is not installed; DAG structure and task logic are tested with mocked modules.
- Triton server/client is not installed; SavedModel output comparison passed.
- Redis server is not available locally; in-memory fallback and fake-client tests passed.
- Two-tower retrieval is implemented with TFRS and FAISS but has Recall@10 = 0.0 and no dedicated tests.
- A/B testing and CTR are simulated only.
- No real click/impression data exists.
- Backend startup takes approximately 60-90 seconds.
- 46 of 137 cached movies still have no verified poster.
- No frontend automated tests exist.
- No CI pipeline is configured.

## 7. Prioritized actions before November 20, 2026

P0:
1. Run a final manual end-to-end demo: backend startup, frontend load, recommendations, search, metrics, and mobile layout.
2. Confirm all documentation uses 50 passed / 3 warnings and the verified metrics above.
3. Keep CF SVD as the production retrieval default.

P1:
1. Document Spark, Airflow, Triton, Redis, two-tower, A/B, and CTR limitations clearly.
2. Add a reproducible latency benchmark script if latency will be cited in the final report.
3. Add integration tests for Redis, Triton, Airflow, and FAISS if time permits.

P2:
1. Improve poster coverage beyond the current 91 verified posters.
2. Add frontend automated tests.
3. Improve ranking experiments and re-evaluate with the same protocol.
4. Persist two-tower user-side artifacts and configuration metadata.

## 8. Final submission-readiness verdict

The project is **ready for final submission as an MVP**. Core data preparation, chronological splitting, CF SVD retrieval, API, frontend, tests, and documentation are implemented and verified. Optional infrastructure components are implemented but not fully integration-verified and must be presented as partial or unverified. CF SVD remains the production retrieval default because measured results show that the deep ranker and pairwise ranker do not improve Recall@10.