from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from src.airflow_tasks import (
    validate_input_data,
    preprocess_interactions,
    train_cf_svd_candidate,
    evaluate_candidate,
    check_acceptance,
    promote_model,
    record_run_status,
)

default_args = {
    "owner": "recommendation-engine",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

with DAG(
    dag_id="cf_svd_retraining",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["recommendation", "cf-svd"],
) as dag:
    validate_input_data_task = PythonOperator(task_id="validate_input_data", python_callable=validate_input_data)
    preprocess_interactions_task = PythonOperator(task_id="preprocess_interactions", python_callable=preprocess_interactions)
    train_candidate_task = PythonOperator(task_id="train_cf_svd_candidate", python_callable=train_cf_svd_candidate)
    evaluate_candidate_task = PythonOperator(task_id="evaluate_candidate", python_callable=evaluate_candidate)
    acceptance_check_task = PythonOperator(task_id="check_acceptance", python_callable=check_acceptance)
    promote_model_task = PythonOperator(task_id="promote_model", python_callable=promote_model)
    record_run_status_task = PythonOperator(task_id="record_run_status", python_callable=record_run_status)
    validate_input_data_task >> preprocess_interactions_task >> train_candidate_task >> evaluate_candidate_task >> acceptance_check_task >> promote_model_task >> record_run_status_task
