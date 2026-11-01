import importlib.util
for mod in ["redis","faiss","pyspark","airflow","tritonclient"]:
    print(mod, bool(importlib.util.find_spec(mod)))
