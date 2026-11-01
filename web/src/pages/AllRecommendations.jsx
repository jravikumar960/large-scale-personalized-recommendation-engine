import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api.js";
import MovieCard from "../components/MovieCard.jsx";

const MAX_RECOMMENDATIONS = 100;

export default function AllRecommendations() {
  const [userId, setUserId] = useState("1");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load(requestedUserId = userId) {
    setLoading(true);
    setError("");
    try {
      setData(await api.recommendations(Number(requestedUserId), MAX_RECOMMENDATIONS));
    } catch (e) {
      setError(e.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load("1");
  }, []);

  const recommendations = data?.recommendations || [];

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>All Recommendations</h1>
          <p>Complete recommendation list returned by the live backend for one user.</p>
        </div>
        <Link className="button secondary" to="/">Back to Dashboard</Link>
      </div>

      <div className="toolbar">
        <label>
          User ID
          <input value={userId} onChange={(e) => setUserId(e.target.value)} />
        </label>
        <button onClick={() => load()} disabled={loading}>
          {loading ? "Loading..." : "Load recommendations"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && (
        <div className="skeleton-grid">
          {Array.from({ length: 8 }).map((_, index) => (
            <div className="skeleton-card" key={index}></div>
          ))}
        </div>
      )}

      {data && (
        <div>
          <p className="muted">
            User {data.user_id} - {data.count} of up to {MAX_RECOMMENDATIONS} recommendations
            {data.cached ? " (cached by backend)" : ""}
          </p>
          <div className="movie-grid">
            {recommendations.map((movie) => (
              <MovieCard movie={movie} key={movie.movie_id} />
            ))}
          </div>
          {recommendations.length === 0 && (
            <div className="empty-state">No recommendations were returned for this user.</div>
          )}
        </div>
      )}
    </section>
  );
}