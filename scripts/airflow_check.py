import airflow
print("file", airflow.__file__)
print("version", getattr(airflow, "__version__", "unknown"))
print("attrs", [x for x in dir(airflow) if "Dag" in x or "Task" in x])
