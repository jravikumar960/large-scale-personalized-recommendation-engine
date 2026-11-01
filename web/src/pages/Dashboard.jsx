import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api.js";
import MovieCard from "../components/MovieCard.jsx";

export default function Dashboard({ health }) {
  const [recommended, setRecommended] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([api.recommendations(1, 8), api.search("", "", 12), api.metrics()])
      .then(([recs, search, metricData]) => {
        if (!active) return;
        setRecommended(recs.recommendations || []);
        setCatalog(search.results || []);
        setMetrics(metricData);
      })
      .catch((e) => { if (active) setError(e.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const hero = recommended[0];

  return (
    <section className="page cinematic">
      <div className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Personalized discovery</span>
          <h1>Discover your next favorite movie</h1>
          <p>Live recommendations, offline validation metrics, and model health from the existing backend.</p>
          <div className="hero-actions">
            <Link className="button primary" to="/for-you">Explore Recommendations</Link>
            <Link className="button secondary" to="/discover">Discover Movies</Link>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          {hero?.poster_url ? <img src={hero.poster_url} alt={hero.title} className="hero-poster" onError={(e) => { e.currentTarget.style.display = "none"; }} /> : null}
          <div className="hero-glow"></div>
          <div className="hero-title">{hero ? hero.title : "Cinematic recommendations"}</div>
        </div>
      </div>
      {error && <div className="error-banner">{error}</div>}
      <div className="section">
        <div className="section-heading">
          <h2>Recommended for You</h2>
          <Link to="/all-recommendations">View all</Link>
        </div>
        {loading ? <div className="loading">Loading recommendations...</div> : (
          <div className="movie-row">
            {recommended.map((movie) => <MovieCard movie={movie} key={movie.movie_id} />)}
          </div>
        )}
      </div>
      <div className="section">
        <div className="section-heading">
          <h2>Popular Picks</h2>
        </div>
        {loading ? <div className="loading">Loading catalog...</div> : (
          <div className="movie-row">
            {catalog.map((movie) => <MovieCard movie={movie} key={movie.movie_id} />)}
          </div>
        )}
      </div>
    </section>
  );
}
