import { useState } from "react";
import { api } from "../lib/api.js";
import MovieCard from "../components/MovieCard.jsx";

const GENRES = ["Action","Adventure","Animation","Children","Comedy","Crime","Documentary","Drama","Fantasy","Film-Noir","Horror","IMAX","Musical","Mystery","Romance","Sci-Fi","Thriller","War","Western"];

export default function Explore() {
  const [query, setQuery] = useState("");
  const [genre, setGenre] = useState("");
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function search() {
    setLoading(true);
    setError("");
    try {
      const data = await api.search(query, genre, 24);
      setResults(data.results || []);
    } catch (e) {
      setError(e.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetails(movieId) {
    try {
      setSelected(await api.item(movieId));
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Discover Movies</h1>
          <p>Search the MovieLens catalog by title or genre.</p>
        </div>
      </div>
      <div className="toolbar search-row">
        <label className="search-field">
          Search
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by title" />
        </label>
        <button className="btn btn-primary search-button" onClick={search} disabled={loading}>{loading ? "Searching..." : "Search"}</button>
      </div>
      <div className="chip-row">
        <button className={genre === "" ? "chip active" : "chip"} onClick={() => setGenre("")}>All genres</button>
        {GENRES.map((g) => (
          <button key={g} className={genre === g ? "chip active" : "chip"} onClick={() => setGenre(g)}>{g}</button>
        ))}
      </div>
      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="skeleton-grid">{Array.from({ length: 8 }).map((_, i) => <div className="skeleton-card" key={i}></div>)}</div>}
      {!loading && results.length === 0 && <div className="empty-state">No movies found for this search.</div>}
      <div className="movie-grid">
        {results.map((movie) => (
          <button className="card-button" key={movie.movie_id} onClick={() => loadDetails(movie.movie_id)}>
            <MovieCard movie={movie} />
          </button>
        ))}
      </div>
      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>{selected.title}</h2>
            <p>{selected.genres}</p>
            <span>Movie ID: {selected.item_id}</span>
            <button className="secondary" onClick={() => setSelected(null)}>Close</button>
          </div>
        </div>
      )}
    </section>
  );
}
