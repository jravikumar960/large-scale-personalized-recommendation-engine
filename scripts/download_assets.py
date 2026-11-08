import os
from pathlib import Path
from huggingface_hub import snapshot_download

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPO_ID = os.getenv(
    "HF_REPO_ID",
    "jravikumar960/recommendation-engine-models"
)

FILES = [
    "models/recommender.joblib",
    "models/metrics.json",
    "models/poster_cache.json",
    "models/cf_svd/config.json",
    "models/cf_svd/item_factors.npy",
    "models/cf_svd/item_ids.json",
    "models/cf_svd/popularity.json",
    "models/cf_svd/user_factors.npy",
    "models/cf_svd/user_ids.json",
    "data/processed/movies.csv",
    "data/raw/movielens/links.csv",
]

def missing_files():
    return [
        file for file in FILES
        if not (PROJECT_ROOT / file).is_file()
    ]

missing = missing_files()

if missing:
    token = os.getenv("HF_TOKEN")

    if not token:
        raise RuntimeError(
            "HF_TOKEN is missing. Set it in the deployment environment."
        )

    print(f"Downloading {len(missing)} missing assets from {REPO_ID}...")

    snapshot_download(
        repo_id=REPO_ID,
        repo_type="model",
        token=token,
        local_dir=str(PROJECT_ROOT),
        allow_patterns=FILES,
    )
else:
    print("All recommendation assets already exist. Skipping download.")

missing = missing_files()

if missing:
    raise RuntimeError(f"Missing required assets: {missing}")

print("SUCCESS: All 11 recommendation assets are ready.")
