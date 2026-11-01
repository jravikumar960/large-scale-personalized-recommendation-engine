import pandas as pd
l = pd.read_csv("data/raw/movielens/links.csv")
print(l.head().to_string(index=False))
print("rows", len(l))
print("cols", list(l.columns))
print("tmdb non-null", l.tmdbId.notna().sum())
