from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from src.cf_svd import train_svd

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--output-dir", default="models/cf_svd")
    parser.add_argument("--k", type=int, default=38)
    args=parser.parse_args()
    data_dir=Path(args.data_dir)
    train=pd.read_csv(data_dir/"train.csv")
    train_svd(train, args.output_dir, k=args.k)
    print("Saved CF SVD to", args.output_dir)

if __name__=="__main__":
    main()
