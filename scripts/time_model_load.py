import time
t=time.perf_counter()
from app.main import get_model
m=get_model()
print("load_seconds", round(time.perf_counter()-t,3))
print("cf_loaded", m.cf_retriever is not None)
print("deep_loaded", m.deep_rank_model is not None)
