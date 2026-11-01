from __future__ import annotations
import csv
import json
import numpy as np
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def _env(name, default):
    return os.getenv(name, default)

def _run_python(module_or_script, *args):
    if module_or_script.endswith(".py"):
        command = [sys.executable, str(PROJECT_ROOT / module_or_script), *args]
    else:
        command = [sys.executable, "-m", module_or_script, *args]
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)

def validate_input_data(input_dir=None):
    input_dir = Path(input_dir or _env("MOVIELENS_INPUT_DIR", str(PROJECT_ROOT / "data" / "raw" / "movielens")))
    ratings_path = input_dir / "ratings.csv"
    movies_path = input_dir / "movies.csv"
    if not ratings_path.is_file() or not movies_path.is_file():
        raise FileNotFoundError(f"Missing required input files in {input_dir}")
    with ratings_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["userId", "movieId", "rating", "timestamp"]:
            raise ValueError(f"Unexpected ratings schema: {reader.fieldnames}")
        if next(reader, None) is None:
            raise ValueError("ratings.csv contains no data rows")
    with movies_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is not None and not {"movieId", "title", "genres"}.issubset(reader.fieldnames):
            raise ValueError(f"Unexpected movies schema: {reader.fieldnames}")
        if next(reader, None) is None:
            raise ValueError("movies.csv contains no data rows")
    return {"input_dir": str(input_dir), "status": "valid"}

def preprocess_interactions(input_dir=None, output_dir=None, test_days=30, validation_days=7):
    input_dir = input_dir or _env("MOVIELENS_INPUT_DIR", str(PROJECT_ROOT / "data" / "raw" / "movielens"))
    output_dir = output_dir or _env("PROCESSED_DATA_DIR", str(PROJECT_ROOT / "data" / "processed"))
    _run_python("src.prepare_data", "--input-dir", str(input_dir), "--output-dir", str(output_dir), "--test-days", str(test_days), "--validation-days", str(validation_days))
    return {"output_dir": str(output_dir)}

def train_cf_svd_candidate(data_dir=None, candidate_dir=None, k=38):
    data_dir = data_dir or _env("PROCESSED_DATA_DIR", str(PROJECT_ROOT / "data" / "processed"))
    candidate_dir = candidate_dir or _env("CF_SVD_CANDIDATE_DIR", str(PROJECT_ROOT / "models" / "cf_svd_candidate"))
    _run_python("src.train_cf_svd", "--data-dir", str(data_dir), "--output-dir", str(candidate_dir), "--k", str(k))
    return {"candidate_dir": str(candidate_dir)}

def evaluate_candidate(data_dir=None, candidate_dir=None, output_path=None, users=500):
    data_dir = data_dir or _env("PROCESSED_DATA_DIR", str(PROJECT_ROOT / "data" / "processed"))
    candidate_dir = candidate_dir or _env("CF_SVD_CANDIDATE_DIR", str(PROJECT_ROOT / "models" / "cf_svd_candidate"))
    output_path = output_path or _env("CF_SVD_CANDIDATE_METRICS", str(PROJECT_ROOT / "models" / "cf_svd_candidate_metrics.json"))
    _run_python("scripts/evaluate_cf_svd.py", "--data-dir", str(data_dir), "--model-dir", str(candidate_dir), "--output", str(output_path), "--users", str(users))
    return {"metrics_path": str(output_path)}

def check_acceptance(metrics_path=None, min_recall_at_10=0.04):
    metrics_path = Path(metrics_path or _env("CF_SVD_CANDIDATE_METRICS", str(PROJECT_ROOT / "models" / "cf_svd_candidate_metrics.json")))
    if not metrics_path.is_file():
        raise FileNotFoundError(f"Candidate metrics not found: {metrics_path}")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    recall = float(metrics.get("cf_svd", {}).get("recall@10", 0.0))
    if recall < min_recall_at_10:
        raise ValueError(f"Candidate failed acceptance: Recall@10={recall} < {min_recall_at_10}")
    (metrics_path.parent / "acceptance_passed.json").write_text(json.dumps({"passed": True, "recall@10": recall, "threshold": min_recall_at_10}, indent=2), encoding="utf-8")
    return metrics

def promote_model(candidate_dir=None, approved_dir=None):
    candidate_dir = Path(candidate_dir or _env("CF_SVD_CANDIDATE_DIR", str(PROJECT_ROOT / "models" / "cf_svd_candidate")))
    approved_dir = Path(approved_dir or _env("CF_SVD_APPROVED_DIR", str(PROJECT_ROOT / "models" / "cf_svd")))
    marker = candidate_dir.parent / "acceptance_passed.json"
    if candidate_dir == approved_dir:
        raise ValueError("Candidate and approved model directories must be different")
    if not marker.is_file():
        raise RuntimeError("Promotion attempted without a successful acceptance check")
    marker_data = json.loads(marker.read_text(encoding="utf-8"))
    if not marker_data.get("passed"):
        raise RuntimeError("Candidate did not pass acceptance checks")
    if approved_dir.exists():
        shutil.rmtree(approved_dir)
    shutil.copytree(candidate_dir, approved_dir)
    return {"approved_dir": str(approved_dir)}

def record_run_status(metrics_path=None, candidate_dir=None, approved_dir=None, status="completed"):
    metrics_path = Path(metrics_path or _env("CF_SVD_CANDIDATE_METRICS", str(PROJECT_ROOT / "models" / "cf_svd_candidate_metrics.json")))
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.is_file() else {}
    manifest = {
        "status": status,
        "metrics": metrics,
        "candidate_dir": str(candidate_dir or _env("CF_SVD_CANDIDATE_DIR", str(PROJECT_ROOT / "models" / "cf_svd_candidate"))),
        "approved_dir": str(approved_dir or _env("CF_SVD_APPROVED_DIR", str(PROJECT_ROOT / "models" / "cf_svd"))),
    }
    output = Path(_env("AIRFLOW_RUN_MANIFEST", str(PROJECT_ROOT / "models" / "airflow_run_manifest.json")))
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
