
# Large-Scale Personalized Recommendation Engine (AIML-03)

CPU-friendly MVP plus validated CF SVD retrieval, FastAPI serving, deep ranker, and optional two-tower artifacts.

## Setup (Windows PowerShell)

```powershell
cd recommendation-engine
& "..\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& "..\.venv\Scripts\python.exe" scripts\make_demo_data.py
& "..\.venv\Scripts\python.exe" -m src.prepare_data --input-dir data\raw\movielens --output-dir data\processed --test-days 30 --validation-days 7
& "..\.venv\Scripts\python.exe" -m src.train --data-dir data\processed --model-dir models
& "..\.venv\Scripts\python.exe" -m src.train_cf_svd --data-dir data\processed --output-dir models\cf_svd --k 38
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for API documentation.

## MovieLens 25M

Extract ratings.csv, movies.csv, tags.csv, and links.csv into data/raw/movielens.

## API

- GET /health
- GET /recommendations/{user_id}?k=10
- GET /items/{item_id}
- GET /movies/{movie_id}
- GET /metrics

## Model inference flow

1. CF SVD retrieval is used when artifacts are available.
2. The deep Keras ranker scores retrieved candidates when available.
3. Gradient boosting and popularity heuristic remain fallbacks.
4. Unknown users use popularity fallback.

## Evaluation

CF SVD on 500 validation users: Recall@10=0.05095, NDCG@10=0.04515, HitRate@10=0.144, Precision@10=0.02420.
Popularity on the same 500 users: Recall@10=0.01400, NDCG@10=0.02020, HitRate@10=0.098, Precision@10=0.01800.
100-user ranking comparison: CF SVD Recall@10=0.04552; popularity Recall@10=0.01586; deep ranker Recall@10=0.00908.
Two-tower retrieval Recall@10=0.0 on 50 eligible users.
Latency was measured locally with 20 sequential requests: median 1.52 ms, p95 3.95 ms.

## Limitations

Spark, Airflow, and Triton are templates or unverified. Redis server connectivity is not verified. A/B testing and CTR are simulated or unavailable. Two-tower retrieval currently has zero Recall@10.

## Tests

& "..\.venv\Scripts\python.exe" -m pytest -q

Result: 50 passed, 3 warnings.
## Frontend
cd web; npm install; npm run dev
Frontend URL: http://localhost:5173
Optional poster metadata: set TMDB_API_KEY before starting the backend.
## Spark preprocessing
Command: $env:JAVA_HOME="C:\Users\jravi\.jdks\openjdk-23.0.2"; $env:HADOOP_HOME="C:\hadoop"; & "..\.venv\Scripts\python.exe" -m src.spark_pipeline ...
Verified on synthetic data: 2 tests passed.
Full MovieLens run was attempted but blocked by Windows Hadoop native library (winutils/hadoop.dll) and Python worker memory limits.
## Redis caching
Set REDIS_URL to use Redis. If unavailable, in-memory fallback is used.
See docs/redis.md.
## Triton model serving
Model repository: triton/model_repository/deep_ranker
Artifact: SavedModel exported from models/deep_ranker/deep_ranker.keras
Verified locally by loading the SavedModel and comparing outputs to Keras.
tritonserver and tritonclient are not installed; real server inference is not verified.
## Airflow retraining DAG
DAG file: airflow/dags/retraining.py
Tasks: validate_input_data, preprocess_interactions, train_cf_svd_candidate, evaluate_candidate, check_acceptance, promote_model, record_run_status
Promotion requires Recall@10 >= 0.04 and valid metrics.
Airflow is not installed as a runnable runtime in this environment; DAG structure is unit-tested with mocked Airflow modules.
## Environment variables

- `TMDB_API_KEY`: optional TMDB poster lookup key. If unset, Wikipedia fallback is used.
- `REDIS_URL`: optional Redis connection URL. If unset or unavailable, in-memory caching is used.
- `RECOMMENDER_MODEL_PATH`, `RECOMMENDER_METRICS_PATH`, `DEEP_RANKER_PATH`, `CF_SVD_PATH`: optional model artifact path overrides.
- `VITE_API_BASE_URL`: optional frontend API base URL. Defaults to `http://127.0.0.1:8000`.

## Verified evaluation summary

- CF SVD on 500 validation users: Recall@10=0.05095, Recall@20=0.06959, NDCG@10=0.04515, HitRate@10=0.144, Precision@10=0.02420.
- Popularity on the same 500 users: Recall@10=0.01400, NDCG@10=0.02020.
- Two-tower retrieval Recall@10=0.0 on 50 eligible users.
- Backend tests: 50 passed, 3 warnings.
- Frontend production build: passed.

  ##Screen Shots

  ##Dashboard
  <img width="1917" height="747" alt="image" src="https://github.com/user-attachments/assets/ce7904a9-cb72-494a-91c3-f6e7e6e0cedc" />

  ##Recommendations
  <img width="1913" height="923" alt="image" src="https://github.com/user-attachments/assets/b9045a09-73ee-4f06-a9ab-7801aee7fee9" />

  ##Discovery
  <img width="1910" height="903" alt="image" src="https://github.com/user-attachments/assets/d919a362-1447-49b8-8612-9081cf4d7345" />

  ##Compare Users
  <img width="1917" height="923" alt="image" src="https://github.com/user-attachments/assets/5d790ee4-8e24-4995-bd00-45ca229b9f44" />

  #Model Insights
  <img width="1917" height="937" alt="image" src="https://github.com/user-attachments/assets/2ca7d271-fba2-4811-8198-696f90990f50" />
  




