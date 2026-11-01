import { useEffect, useState } from "react";

function releaseYear(title) {
  const match = (title || "").match(/\((\d{4})\)/);
  return match ? match[1] : null;
}

function fallbackLabel(movie) {
  const title = (movie.title || "Movie").trim();
  return title.length > 28 ? `${title.slice(0, 25)}...` : title;
}

export default function MovieCard({ movie, compact = false }) {
  const genres = (movie.genres || "").split("|").filter(Boolean);
  const year = releaseYear(movie.title);
  const [posterUrl, setPosterUrl] = useState(movie.poster_url || null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setPosterUrl(movie.poster_url || null);
    setFailed(false);
  }, [movie.poster_url, movie.title]);

  function handleError() {
    if (!failed) {
      setFailed(true);
      setPosterUrl(null);
    }
  }

  return (
    <article className={`movie-card ${compact ? "compact" : ""}`}>
      <div className="poster">
        {posterUrl ? (
          <img src={posterUrl} alt={`${movie.title} poster`} loading="lazy" onError={handleError} />
        ) : (
          <div className="poster-fallback" aria-label={`${movie.title} poster unavailable`}>
            <span>{fallbackLabel(movie)}</span>
            <small>Poster unavailable</small>
          </div>
        )}
        {movie.score !== undefined && <div className="score-pill">{Number(movie.score).toFixed(2)}</div>}
      </div>
      <div className="movie-body">
        <h3 title={movie.title}>{movie.title}</h3>
        {year && <p className="year">{year}</p>}
        <div className="genre-row">
          {genres.map((genre) => (
            <span className="genre-chip" key={genre}>{genre}</span>
          ))}
        </div>
        <div className="movie-meta">
          <span>ID {movie.movie_id ?? movie.item_id}</span>
          {movie.cached !== undefined && <span>{movie.cached ? "Cached" : "Fresh"}</span>}
        </div>
      </div>
    </article>
  );
}
