import json
from pathlib import Path
import pytest
from src.airflow_tasks import validate_input_data, check_acceptance, promote_model, record_run_status

def test_validate_input_data_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_input_data(str(tmp_path / "missing"))

def test_check_acceptance_failure(tmp_path):
    metrics = tmp_path / "metrics.json"
    metrics.write_text(json.dumps({"cf_svd": {"recall@10": 0.01}}), encoding="utf-8")
    with pytest.raises(ValueError):
        check_acceptance(str(metrics), min_recall_at_10=0.04)

def test_check_acceptance_success(tmp_path):
    metrics = tmp_path / "metrics.json"
    metrics.write_text(json.dumps({"cf_svd": {"recall@10": 0.05}}), encoding="utf-8")
    result = check_acceptance(str(metrics), min_recall_at_10=0.04)
    assert result["cf_svd"]["recall@10"] == 0.05
    assert (tmp_path / "acceptance_passed.json").is_file()

def test_promote_requires_acceptance(tmp_path):
    candidate = tmp_path / "candidate"
    approved = tmp_path / "approved"
    candidate.mkdir()
    (candidate / "model.txt").write_text("candidate", encoding="utf-8")
    with pytest.raises(RuntimeError):
        promote_model(str(candidate), str(approved))

def test_promote_copies_after_acceptance(tmp_path):
    candidate = tmp_path / "candidate"
    approved = tmp_path / "approved"
    candidate.mkdir()
    (candidate / "model.txt").write_text("candidate", encoding="utf-8")
    (candidate.parent / "acceptance_passed.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    result = promote_model(str(candidate), str(approved))
    assert Path(result["approved_dir"]).is_dir()
    assert (approved / "model.txt").read_text(encoding="utf-8") == "candidate"

def test_record_run_status(tmp_path, monkeypatch):
    metrics = tmp_path / "metrics.json"
    metrics.write_text(json.dumps({"cf_svd": {"recall@10": 0.05}}), encoding="utf-8")
    monkeypatch.setenv("AIRFLOW_RUN_MANIFEST", str(tmp_path / "manifest.json"))
    manifest = record_run_status(str(metrics), str(tmp_path / "candidate"), str(tmp_path / "approved"))
    assert manifest["status"] == "completed"
    assert (tmp_path / "manifest.json").is_file()
