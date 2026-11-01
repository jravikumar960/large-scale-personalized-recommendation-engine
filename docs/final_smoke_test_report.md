# Final Live Application Smoke Test Report

## Backend startup
- Command: `& "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Result: Started successfully after approximately 90 seconds.
- Health endpoint returned `200 OK` with `model_loaded=true`, `deep_ranker_loaded=true`, `cf_svd_loaded=true`, and `cf_svd_error=null`.

## Endpoints tested

| Endpoint | HTTP status | Result |
|---|---:|---|
| `GET /health` | 200 | Backend healthy; CF SVD and deep ranker loaded |
| `GET /recommendations/1?k=10` | 200 | Returned 10 recommendations with fields `movie_id`, `title`, `genres`, `score`, `poster_url` |
| `GET /recommendations/999999?k=3` | 200 | Unknown user returned 3 popularity-based recommendations |
| `GET /items/1` | 200 | Item details returned |
| `GET /movies/1` | 200 | Movie details returned |
| `GET /movies/search?q=toy&limit=5` | 200 | Returned 5 results including `Toy Story (1995)` |
| `GET /movies/search?q=matrix&limit=3` | 200 | Returned 3 Matrix-related results |
| `GET /metrics` | 200 | Returned evaluation metrics JSON |
| `GET /docs` | 200 | Swagger UI HTML returned |
| CORS preflight from `http://127.0.0.1:5173` | 200 | `Access-Control-Allow-Origin: http://127.0.0.1:5173` |

## Frontend startup
- Command: `npm run dev -- --host 127.0.0.1` from `recommendation-engine/web`
- Result: Vite dev server started and `http://127.0.0.1:5173` returned `200 OK`.

## Browser verification
Browser automation was not available (no Playwright/Selenium installed). Therefore, interactive UI behavior was not manually exercised. The following were verified indirectly:
- Frontend dev server responds with HTTP 200.
- Frontend production build passed during the prior audit.
- Backend API responses required by the frontend are valid and CORS-enabled.
- API client uses `http://127.0.0.1:8000` by default.

## Failures
No endpoint failures occurred during the live smoke test.

## Files changed
No application or model files were changed during this smoke test. This report was created:
- `docs/final_smoke_test_report.md`

## Remaining limitations
- Interactive browser checks (dashboard rendering, recommendation loading, search interaction, poster rendering, metrics page, mobile layout) were not actually performed.
- Backend startup takes approximately 90 seconds due to loading the serialized model artifact.
- Real Redis, Triton, Airflow, and Spark integrations remain unverified.
- Two-tower retrieval remains experimental with zero Recall@10.
- CTR and live A/B testing remain simulated only.

## Demo readiness
The application is ready for a recorded backend/API demo. For a full UI demo, perform a manual browser walkthrough before recording because interactive UI behavior was not verified in this environment.