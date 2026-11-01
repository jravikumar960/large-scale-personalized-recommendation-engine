import sys, types, importlib.util
def _install_fake_airflow():
    airflow = types.ModuleType("airflow")
    models = types.ModuleType("airflow.models")
    operators = types.ModuleType("airflow.operators")
    python = types.ModuleType("airflow.operators.python")
    created = []
    class DAG:
        pass
    class PythonOperator:
        pass
    models.DAG = DAG
    python.PythonOperator = PythonOperator
    airflow.models = models
    airflow.operators = operators
    operators.python = python
    sys.modules["airflow"] = airflow
    sys.modules["airflow.models"] = models
    sys.modules["airflow.operators"] = operators
    sys.modules["airflow.operators.python"] = python
    return created
def test_debug():
    print("BEFORE", sys.modules.get("airflow"))
    created = _install_fake_airflow()
    print("AFTER", sys.modules.get("airflow"), sys.modules["airflow"].__dict__.get("DAG"))
    spec = importlib.util.spec_from_file_location("retraining_dag", "airflow/dags/retraining.py")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        print("LOADED")
    except Exception as e:
        print("ERROR", repr(e))
        print("SYS", sys.modules.get("airflow"))
