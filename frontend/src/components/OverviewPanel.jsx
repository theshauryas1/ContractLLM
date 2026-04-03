export default function OverviewPanel({ overview, analyses, onSelectAnalysis }) {
  const items = [
    { label: "Analyses", value: overview?.total_analyses ?? 0 },
    { label: "Requirements", value: overview?.total_requirements ?? 0 },
    { label: "High Risk", value: overview?.high_risk_analyses ?? 0 },
    { label: "Feedback Items", value: overview?.feedback_items ?? 0 }
  ];

  return (
    <>
      <section className="stats-grid">
        {items.map((item) => (
          <article key={item.label} className="stat-card">
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </article>
        ))}
      </section>
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Stored Runs</p>
            <h2>Recent Analyses</h2>
          </div>
          <span className="meta">Avg confidence {(overview?.average_confidence ?? 0).toFixed(2)}</span>
        </div>
        <div className="recent-analysis-list">
          {(analyses ?? []).map((analysis) => (
            <button key={analysis.analysis_id} type="button" className="recent-analysis-item" onClick={() => onSelectAnalysis(analysis.analysis_id)}>
              <strong>{analysis.tender_title}</strong>
              <span>{analysis.tender_language.toUpperCase()} to {analysis.output_language.toUpperCase()}</span>
              <span>Risk {analysis.overall_risk}</span>
              <span>Missing {analysis.missing_count}</span>
            </button>
          ))}
          {!analyses?.length ? <p className="meta">No analyses yet.</p> : null}
        </div>
      </section>
    </>
  );
}
