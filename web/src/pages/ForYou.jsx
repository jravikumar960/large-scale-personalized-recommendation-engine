import { useState, useMemo } from "react";
import { api } from "../lib/api.js";
import MovieCard from "../components/MovieCard.jsx";

export default function ForYou() {
  const [userId, setUserId] = useState("1");
  const [count, setCount] = useState("10");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [genre, setGenre] = useState("All");

  const genres = useMemo(() => {
    const values = new Set();
    data?.recommendations?.forEach((movie) => {
      (movie.genres || "").split("|").filter(Boolean).forEach((g) => values.add(g));
    });
    return ["All", ...Array.from(values).sort()];
  }, [data]);

  const visible = useMemo(() => {
    if (!data?.recommendations) return [];
    if (genre === "All") return data.recommendations;
    return data.recommendations.filter((movie) => (movie.genres || "").includes(genre));
  }, [data, genre]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await api.recommendations(Number(userId), Number(count)));
    } catch (e) {
      setError(e.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Made for You</h1>
          <p>Personalized recommendations from the live backend.</p>
        </div>
      </div>
      <div className="toolbar form-row-made-for-you">
        <label>User ID<input className="control-user-id" value={userId} onChange={(e) => setUserId(e.target.value)} /></label>
        <label>Count<select className="control-count" value={count} onChange={(e) => setCount(e.target.value)}><option value="5">5</option><option value="10">10</option><option value="20">20</option></select></label>
        <button className="btn btn-primary control-submit" onClick={load} disabled={loading} style={{ whiteSpace: "nowrap" }}>{loading ? "Loading..." : "Get recommendations"}</button>
        <button className="btn btn-secondary control-refresh" onClick={load} disabled={loading} style={{ whiteSpace: "nowrap" }}>Refresh</button>
      </div>
      {genres.length > 1 && (
        <div className="chip-row">
          {genres.map((g) => (
            <button key={g} className={genre === g ? "chip active" : "chip"} onClick={() => setGenre(g)}>{g}</button>
          ))}
        </div>
      )}
      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="skeleton-grid">{Array.from({ length: 6 }).map((_, i) => <div className="skeleton-card" key={i}></div>)}</div>}
      {data && (
        <div>
          <p className="muted">User {data.user_id} - {data.count} recommendations{data.cached ? " (cached by backend)" : ""}</p>
          <div className="movie-grid">
            {visible.map((movie) => <MovieCard movie={movie} key={movie.movie_id} />)}
          </div>
          {visible.length === 0 && <div className="empty-state">No recommendations match this genre filter.</div>}
        </div>
      )}
    </section>
  );
}
