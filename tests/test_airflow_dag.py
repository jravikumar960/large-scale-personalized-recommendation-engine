
import importlib.util
import sys
import types

def _install_fake_airflow():
    airflow = types.ModuleType("airflow")
    models = types.ModuleType("airflow.models")
    operators = types.ModuleType("airflow.operators")
    python = types.ModuleType("airflow.operators.python")
    created = []
    class DAG:
        def __init__(self, dag_id, **kwargs):
            self.dag_id = dag_id
            self.kwargs = kwargs
            self.tasks = created
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    class PythonOperator:
        def __init__(self, task_id, python_callable, **kwargs):
            self.task_id = task_id
            self.python_callable = python_callable
            self.kwargs = kwargs
            self.downstream = set()
            self.upstream = set()
            created.append(self)
        def __rshift__(self, other):
            targets = other if isinstance(other, (list, tuple)) else [other]
            for target in targets:
                self.downstream.add(target.task_id)
                target.upstream.add(self.task_id)
            return other if not isinstance(other, (list, tuple)) else targets[-1]
    models.DAG = DAG
    airflow.DAG = DAG
    airflow.DAG = DAG
    airflow.DAG = DAG
    airflow.DAG = DAG
    airflow.DAG = DAG
    airflow.DAG = DAG
    airflow.DAG = DAG
    airflow.DAG = DAG
    python.PythonOperator = PythonOperator
    airflow.models = models
    airflow.operators = operators
    operators.python = python
    sys.modules["airflow"] = airflow
    sys.modules["airflow.models"] = models
    sys.modules["airflow.operators"] = operators
    sys.modules["airflow.operators.python"] = python
    return created

def test_dag_task_ids_and_dependencies():
    created = _install_fake_airflow()
    created.clear()
    spec = importlib.util.spec_from_file_location("retraining_dag", "airflow/dags/retraining.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    task_ids = {task.task_id for task in created}
    expected = {
        "validate_input_data",
        "preprocess_interactions",
        "train_cf_svd_candidate",
        "evaluate_candidate",
        "check_acceptance",
        "promote_model",
        "record_run_status",
    }
    assert task_ids == expected
    by_id = {task.task_id: task for task in created}
    assert by_id["validate_input_data"].downstream == {"preprocess_interactions"}
    assert by_id["preprocess_interactions"].downstream == {"train_cf_svd_candidate"}
    assert by_id["train_cf_svd_candidate"].downstream == {"evaluate_candidate"}
    assert by_id["evaluate_candidate"].downstream == {"check_acceptance"}
    assert by_id["check_acceptance"].downstream == {"promote_model"}
    assert by_id["promote_model"].downstream == {"record_run_status"}
