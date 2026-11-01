import { useEffect, useState } from "react";
import { api } from "../lib/api.js";

function formatMetric(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return Number(value).toFixed(4);
}

function MetricCard({ label, value, note }) {
  return (
    <div className="metric-card insight-metric">
      <span>{label}</span>
      <strong>{formatMetric(value)}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}

function ComparisonBars({ leftLabel, rightLabel, leftValue, rightValue, leftClass, rightClass }) {
  const values = [leftValue || 0, rightValue || 0];
  const max = Math.max(...values, 0.000001);
  const leftWidth = `${((leftValue || 0) / max * 100).toFixed(1)}%`;
  const rightWidth = `${((rightValue || 0) / max * 100).toFixed(1)}%`;
  return (
    <div className="comparison-chart" aria-label={`${leftLabel} versus ${rightLabel}`}>
      <div className="chart-group">
        <div className="chart-group-title">Recall@10</div>
        <div className="chart-row">
          <span className="chart-label">{leftLabel}</span>
          <div className="chart-track"><div className={`chart-bar ${leftClass}`} style={{ width: leftWidth }}></div></div>
          <strong>{formatMetric(leftValue)}</strong>
        </div>
        <div className="chart-row">
          <span className="chart-label">{rightLabel}</span>
          <div className="chart-track"><div className={`chart-bar ${rightClass}`} style={{ width: rightWidth }}></div></div>
          <strong>{formatMetric(rightValue)}</strong>
        </div>
      </div>
    </div>
  );
}

export default function Insights() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api.metrics()
      .then((data) => { if (active) setMetrics(data); })
      .catch((e) => { if (active) setError(e.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const cf = metrics?.cf_svd_validation?.cf_svd;
  const pop = metrics?.cf_svd_validation?.popularity;
  const ranking = metrics?.ranking_comparison || {};
  const deepValidation = metrics?.cf_pop_deep_validation || {};
  const deepCf = deepValidation.cf_svd;
  const deepPopularity = deepValidation.popularity;
  const deepRanker = deepValidation.deep_ranker;

  return (
    <section className="page insights-page">
      <div className="page-header insights-header">
        <div>
          <span className="eyebrow">Machine learning evaluation</span>
          <h1>Model Insights</h1>
          <p>Offline evaluation, retrieval quality, and model limitations.</p>
        </div>
        <span className="status-badge status-primary">Primary retrieval: CF SVD</span>
      </div>

      {loading && <div className="loading">Loading metrics...</div>}
      {error && <div className="error-banner">{error}</div>}

      {metrics && (
        <>
          <section className="insights-section">
            <div className="section-heading">
              <h2>Primary Retrieval — CF SVD</h2>
              <span className="status-badge status-primary">CF SVD</span>
            </div>
            <div className="metric-grid">
              <MetricCard label="Recall@10" value={cf?.["recall@10"]} note="Validation" />
              <MetricCard label="Recall@20" value={cf?.["recall@20"]} note="Validation" />
              <MetricCard label="NDCG@10" value={cf?.["ndcg@10"]} note="Validation" />
              <MetricCard label="HitRate@10" value={cf?.["hit_rate@10"]} note="Validation" />
              <MetricCard label="Precision@10" value={cf?.["precision@10"]} note="Validation" />
            </div>
            <div className="protocol-card">
              <div className="protocol-item"><span>Validation users</span><strong>{cf?.users ?? "N/A"}</strong></div>
              <div className="protocol-item"><span>Candidate universe</span><strong>40,420 items</strong></div>
              <div className="protocol-item"><span>Relevance threshold</span><strong>rating ≥ 4</strong></div>
              <p className="muted">
                Chronological validation split. CF SVD retrieves from the full CF item vocabulary after excluding items already seen by each user.
                Metrics are averaged over eligible validation users only.
              </p>
            </div>
          </section>

          <section className="insights-section">
            <div className="section-heading">
              <h2>CF SVD vs. Popularity Baseline</h2>
              <span className="status-badge status-neutral">500 validation users</span>
            </div>
            <p className="muted">
              Same 500-user validation protocol and 40,420-item candidate universe. Values are the actual saved evaluation results.
            </p>
            <ComparisonBars
              leftLabel="CF SVD"
              rightLabel="Popularity"
              leftValue={cf?.["recall@10"]}
              rightValue={pop?.["recall@10"]}
              leftClass="chart-bar-cyan"
              rightClass="chart-bar-slate"
            />
            <div className="chart-legend">
              <span><i className="legend-dot legend-cyan"></i> CF SVD</span>
              <span><i className="legend-dot legend-slate"></i> Popularity</span>
            </div>
            <div className="metrics-grid compact-metrics">
              <div className="metric-card"><span>CF SVD NDCG@10</span><strong>{formatMetric(cf?.["ndcg@10"])}</strong></div>
              <div className="metric-card"><span>Popularity NDCG@10</span><strong>{formatMetric(pop?.["ndcg@10"])}</strong></div>
              <div className="metric-card"><span>CF SVD HitRate@10</span><strong>{formatMetric(cf?.["hit_rate@10"])}</strong></div>
              <div className="metric-card"><span>Popularity HitRate@10</span><strong>{formatMetric(pop?.["hit_rate@10"])}</strong></div>
            </div>
          </section>
          <section className="insights-section">
            <div className="section-heading">
              <h2>Ranking Experiments</h2>
              <span className="status-badge status-neutral">100 validation users</span>
            </div>
            <p className="muted">
              Candidate-level comparison on 100 eligible held-out users with 200 retrieved candidates and top-10 evaluation.
              These results use a smaller sample than the 500-user retrieval comparison.
            </p>
            <div className="ranking-table-wrap">
              <table className="ranking-table">
                <thead>
                  <tr>
                    <th>Method</th>
                    <th>Recall@10</th>
                    <th>NDCG@10</th>
                    <th>HitRate@10</th>
                    <th>Precision@10</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Popularity ranking</td>
                    <td>{formatMetric(ranking.popularity?.recall_at_10)}</td>
                    <td>{formatMetric(ranking.popularity?.ndcg_at_10)}</td>
                    <td>{formatMetric(ranking.popularity?.hit_rate_at_10)}</td>
                    <td>{formatMetric(ranking.popularity?.precision_at_10)}</td>
                  </tr>
                  <tr>
                    <td>Gradient boosting</td>
                    <td>{formatMetric(ranking.gradient_boosting?.recall_at_10)}</td>
                    <td>{formatMetric(ranking.gradient_boosting?.ndcg_at_10)}</td>
                    <td>{formatMetric(ranking.gradient_boosting?.hit_rate_at_10)}</td>
                    <td>{formatMetric(ranking.gradient_boosting?.precision_at_10)}</td>
                  </tr>
                  <tr>
                    <td>Deep ranker</td>
                    <td>{formatMetric(ranking.deep_ranker?.recall_at_10)}</td>
                    <td>{formatMetric(ranking.deep_ranker?.ndcg_at_10)}</td>
                    <td>{formatMetric(ranking.deep_ranker?.hit_rate_at_10)}</td>
                    <td>{formatMetric(ranking.deep_ranker?.precision_at_10)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="section-heading ranking-subheading">
              <h3>End-to-end retrieval + ranking</h3>
              <span className="status-badge status-neutral">100 validation users</span>
            </div>
            <div className="ranking-table-wrap">
              <table className="ranking-table">
                <thead>
                  <tr>
                    <th>Method</th>
                    <th>Recall@10</th>
                    <th>Recall@20</th>
                    <th>NDCG@10</th>
                    <th>HitRate@10</th>
                    <th>Precision@10</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>CF SVD retrieval alone</td>
                    <td>{formatMetric(deepCf?.["recall@10"])}</td>
                    <td>{formatMetric(deepCf?.["recall@20"])}</td>
                    <td>{formatMetric(deepCf?.["ndcg@10"])}</td>
                    <td>{formatMetric(deepCf?.["hit_rate@10"])}</td>
                    <td>{formatMetric(deepCf?.["precision@10"])}</td>
                  </tr>
                  <tr>
                    <td>CF SVD + deep ranker</td>
                    <td>{formatMetric(deepRanker?.["recall@10"])}</td>
                    <td>{formatMetric(deepRanker?.["recall@20"])}</td>
                    <td>{formatMetric(deepRanker?.["ndcg@10"])}</td>
                    <td>{formatMetric(deepRanker?.["hit_rate@10"])}</td>
                    <td>{formatMetric(deepRanker?.["precision@10"])}</td>
                  </tr>
                  <tr>
                    <td>CF SVD + popularity ranking</td>
                    <td>{formatMetric(deepPopularity?.["recall@10"])}</td>
                    <td>{formatMetric(deepPopularity?.["recall@20"])}</td>
                    <td>{formatMetric(deepPopularity?.["ndcg@10"])}</td>
                    <td>{formatMetric(deepPopularity?.["hit_rate@10"])}</td>
                    <td>{formatMetric(deepPopularity?.["precision@10"])}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="muted">
              CF SVD retrieval alone remains the strongest retrieval baseline. A separate pairwise ranking experiment is documented in
              <code>docs/recommendation_experiments.md</code> and did not improve CF SVD Recall@10.
            </p>
          </section>
        </>
      )}
    </section>
  );
}
