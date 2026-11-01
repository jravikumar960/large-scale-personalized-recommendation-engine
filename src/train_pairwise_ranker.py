from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from src.recommender import TwoStageBaseline
from src.cf_svd import SvdRetriever
from src.pairwise_ranker import train_pairwise_ranker

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--output-dir", default="models/pairwise_ranker")
    parser.add_argument("--sample-size", type=int, default=100000)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    train = pd.read_csv(data_dir / "train.csv")
    movies = pd.read_csv(data_dir / "movies.csv")
    model = TwoStageBaseline().fit(train, movies)
    model.cf_retriever = SvdRetriever("models/cf_svd")
    model.train_ranker(train.sample(n=min(50000, len(train)), random_state=42))
    scorer, history = train_pairwise_ranker(model, train, args.output_dir, sample_size=args.sample_size, seed=args.seed, epochs=args.epochs)
    print("Saved pairwise ranker to", args.output_dir)
    print("epochs", len(history.history["loss"]))

if __name__ == "__main__":
    main()
