from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from src.recommender import TwoStageBaseline
from src.deep_ranker import train_deep_ranker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--output-dir", default="models/deep_ranker")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--sample-size", type=int, default=100000)
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    train = pd.read_csv(data_dir / "train.csv")
    movies = pd.read_csv(data_dir / "movies.csv")
    model = TwoStageBaseline().fit(train, movies)
    model.train_ranker(train.sample(n=min(50000, len(train)), random_state=42))
    deep = train_deep_ranker(train, model, args.output_dir, epochs=args.epochs, sample_size=args.sample_size)
    print("Saved deep ranker to", args.output_dir)


if __name__ == "__main__":
    main()
