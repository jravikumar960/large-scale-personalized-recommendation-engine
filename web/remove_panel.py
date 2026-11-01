p = "src/pages/Dashboard.jsx"
s = open(p).read()
old = """      <div className="panel compact">
        <h2>Model health</h2>
        <div className="health-grid">
          <span>API: {health?.status === "ok" ? "Healthy" : "Unavailable"}</span>
          <span>CF SVD: {health?.cf_svd_loaded ? "Loaded" : "Unavailable"}</span>
          <span>Deep ranker: {health?.deep_ranker_loaded ? "Loaded" : "Unavailable"}</span>
          <span>Version: {health?.model_version || "-"}</span>
        </div>
        {health?.cf_svd_error && <div className="error-banner">{health.cf_svd_error}</div>}
      </div>
"""
s = s.replace(old, "")
open(p, "w").write(s)
print("done")
"""
