import pandas as pd
from src.posters import get_poster_url
movie_ids = [318, 58559, 79132, 109487, 2571, 858, 296, 356, 2959, 4993, 1, 89745, 1721, 480, 593, 1213, 47, 5618, 202439, 112552]
movies = pd.read_csv("data/processed/movies.csv")
for movie_id in movie_ids:
    row = movies[movies.movieId == movie_id].iloc[0]
    poster_url = get_poster_url(int(row.movieId), str(row.title))
    print(f"{movie_id}: {row.title} -> {poster_url}")
