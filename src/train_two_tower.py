from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from src.two_tower import train_two_tower


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--output-dir", default="models/two_tower")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--sample-size", type=int, default=200000)
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    train = pd.read_csv(data_dir / "train.csv")
    movies = pd.read_csv(data_dir / "movies.csv")
    model, index, movie_ids = train_two_tower(train, movies, args.output_dir, epochs=args.epochs, sample_size=args.sample_size)
    print("Trained two-tower. Movies:", len(movie_ids))


if __name__ == "__main__":
    main()
