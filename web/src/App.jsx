import { NavLink, Routes, Route } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "./lib/api.js";
import Dashboard from "./pages/Dashboard.jsx";
import ForYou from "./pages/ForYou.jsx";
import Compare from "./pages/Compare.jsx";
import Explore from "./pages/Explore.jsx";
import Insights from "./pages/Insights.jsx";
import AllRecommendations from "./pages/AllRecommendations.jsx";

export default function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    api.health().then(setHealth).catch((e) => setError(e.message));
  }, []);

  const nav = [
    ["/", "Home"],
    ["/for-you", "For You"],
    ["/discover", "Discover"],
    ["/compare", "Compare Users"],
    ["/insights", "Model Insights"],
  ];

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <div className="brand">
          <button className="menu-toggle" type="button" aria-label="Toggle navigation" onClick={() => setMenuOpen((value) => !value)}>
            <span></span><span></span><span></span>
          </button>
          <span className="brand-mark">AI</span>
          <div>
            <strong>Movie Intelligence</strong>
            <small>Recommendation Console</small>
          </div>
        </div>
        <nav className="sidebar-nav">
          {nav.map(([path, label]) => (
            <NavLink key={path} to={path} end={path === "/"} onClick={() => setMenuOpen(false)}>{label}</NavLink>
          ))}
        </nav>
        <div className="status-pill">
          <span className={health?.status === "ok" ? "dot ok" : "dot"}></span>
          {health ? "Backend connected" : "Checking backend..."}
        </div>
      </aside>
      <div className="main-region">
        <header className="topbar">
          <div>
            <h1>AI Recommendation Engine</h1>
            <p>Personalized discovery powered by live backend models.</p>
          </div>
          <div className="topbar-actions">
            <span className="connection-chip">{health?.cf_svd_loaded ? "CF SVD active" : "CF SVD unavailable"}</span>
          </div>
        </header>
        <main className="content">
          {error && <div className="error-banner">{error}</div>}
          <Routes>
            <Route path="/" element={<Dashboard health={health} />} />
            <Route path="/for-you" element={<ForYou />} />
            <Route path="/discover" element={<Explore />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/all-recommendations" element={<AllRecommendations />} />
            <Route path="/insights" element={<Insights />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
