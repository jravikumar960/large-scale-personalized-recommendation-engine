import pandas as pd
m = pd.read_csv("data/processed/movies.csv")
print(m.head(10).to_string(index=False))
print("rows", len(m))
print("columns", list(m.columns))
genres = sorted({g for row in m.genres.dropna() for g in str(row).split("|") if g and g != "(no genres listed)"})
print("genres", genres)
