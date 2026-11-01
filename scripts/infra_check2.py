import redis
r=redis.Redis(host="localhost",port=6379,socket_timeout=1)
try:
    print("redis ping:", r.ping())
except Exception as e:
    print("redis unavailable:", repr(e))
import airflow
print("airflow", airflow.__file__)
from airflow.models import DagBag
db=DagBag(dag_folder="airflow/dags", include_examples=False)
print("dag import errors:", db.import_errors)
print("dags:", list(db.dags.keys()))
