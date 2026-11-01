import pandas as pd
movies = pd.read_csv("data/processed/movies.csv")
requested = ["Shawshank Redemption", "Dark Knight", "Inception", "Interstellar", "Matrix", "Godfather", "Pulp Fiction", "Forrest Gump", "Fight Club", "Fellowship of the Ring", "Toy Story", "Avengers", "Titanic", "Jurassic Park", "Silence of the Lambs", "Goodfellas", "Se7en", "Spirited Away", "Parasite", "Whiplash"]
for needle in requested:
    matches = movies[movies.title.str.contains(needle, case=False, regex=False)]
    print("\n" + needle)
    print(matches[["movieId", "title", "genres"]].head(5).to_string(index=False))
