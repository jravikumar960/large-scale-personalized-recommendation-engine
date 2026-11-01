Implementation status
1. MovieLens 25M: implemented and tested
2. Temporal split: implemented and tested
3. Spark preprocessing: implemented and tested on synthetic data; full MovieLens run blocked by Windows Hadoop/Python worker environment
4. TFRS two-tower: implemented; artifact and FAISS index validated; retrieval Recall@10 = 0.0
5. FAISS item retrieval: implemented and tested for two-tower
6. Deep ranking model: implemented, integrated, evaluated
7. Cold-start fallback: implemented and tested
8. Redis caching: implemented; unit tests pass; real server unavailable locally
9. Triton serving: SavedModel and config verified; tritonserver/tritonclient not installed
10. Airflow workflow: DAG implemented and structure-tested; Airflow runtime not installed
11. A/B testing: simulated framework only
12. Metrics: Recall, NDCG, HitRate, Precision implemented; CTR unavailable without click data
13. FastAPI: implemented and tested
14. Frontend: implemented and production build verified
Tests: 50 passed, 3 warnings
