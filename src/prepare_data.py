from __future__ import annotations
import argparse
from pathlib import Path
from src.data import load_movielens, temporal_split


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate MovieLens CSVs and create a temporal split")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--test-days", type=int, default=30)
    parser.add_argument("--validation-days", type=int, default=7)
    args = parser.parse_args()
    ratings, movies = load_movielens(args.input_dir)
    train, val, test, val_cutoff, test_cutoff = temporal_split(ratings, args.test_days, args.validation_days)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    train.to_csv(output / "train.csv", index=False)
    val.to_csv(output / "validation.csv", index=False)
    test.to_csv(output / "test.csv", index=False)
    movies.to_csv(output / "movies.csv", index=False)
    (output / "split_manifest.txt").write_text(
        f"validation_cutoff_timestamp={val_cutoff}\n"
        f"test_cutoff_timestamp={test_cutoff}\n"
        f"train_rows={len(train)}\nvalidation_rows={len(val)}\ntest_rows={len(test)}\nmovie_rows={len(movies)}\n",
        encoding="utf-8",
    )
    print(f"Saved temporal split: train={len(train):,}, validation={len(val):,}, test={len(test):,}, movies={len(movies):,}")


if __name__ == "__main__":
    main()
