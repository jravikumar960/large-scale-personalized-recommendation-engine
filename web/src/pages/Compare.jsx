import { useState } from "react";
import { api } from "../lib/api.js";
import MovieCard from "../components/MovieCard.jsx";

function Column({ accent, userId, data }) {
  return (
    <div className={`compare-column ${accent}`}>
      <div className="compare-user-header">
        <span className="compare-user-label">{accent === "user-accent-a" ? "USER 1" : "USER 2"}</span>
        {userId && <span className="compare-user-id">User ID {userId}</span>}
      </div>
      <p className="compare-user-subtitle">Personalized recommendations</p>
      {data ? (
        <div className="movie-grid compact">
          {data.recommendations.map((movie) => <MovieCard movie={movie} compact key={movie.movie_id} />)}
        </div>
      ) : <div className="empty-state">No recommendations loaded.</div>}
    </div>
  );
}

export default function Compare() {
  const [userA, setUserA] = useState("1");
  const [userB, setUserB] = useState("2");
  const [count, setCount] = useState("10");
  const [dataA, setDataA] = useState(null);
  const [dataB, setDataB] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [a, b] = await Promise.all([api.recommendations(Number(userA), Number(count)), api.recommendations(Number(userB), Number(count))]);
      setDataA(a);
      setDataB(b);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Compare Users</h1>
          <p>Retrieve recommendations for two user IDs and compare the results.</p>
        </div>
      </div>
      <div className="toolbar compare-row">
        <label>User A<input className="control-user-a" value={userA} onChange={(e) => setUserA(e.target.value)} /></label>
        <label>User B<input className="control-user-b" value={userB} onChange={(e) => setUserB(e.target.value)} /></label>
        <label>Count<select className="control-count" value={count} onChange={(e) => setCount(e.target.value)}><option value="5">5</option><option value="10">10</option><option value="20">20</option></select></label>
        <button className="btn btn-secondary control-compare" onClick={load} disabled={loading}>{loading ? "Loading..." : "Compare"}</button>
      </div>
      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="loading">Loading recommendations...</div>}
      <div className="compare-grid">
        <Column accent="user-accent-a" userId={userA} data={dataA} />
        <Column accent="user-accent-b" userId={userB} data={dataB} />
      </div>
      <p className="muted">Different histories can produce different lists, but list differences alone do not prove recommendation quality.</p>
    </section>
  );
}
