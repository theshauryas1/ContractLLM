export default function RiskPanel({ risks }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Risk Agent</p>
          <h2>Risk Flags</h2>
        </div>
      </div>
      <div className="risk-grid">
        {(risks ?? []).map((risk) => (
          <article key={`${risk.requirement_id}-${risk.severity}`} className={`risk-card risk-${risk.severity}`}>
            <span className="trace-chip">{risk.severity}</span>
            <h3>{risk.title}</h3>
            <p>{risk.rationale}</p>
            <p className="meta">{risk.mitigation}</p>
          </article>
        ))}
        {!risks?.length ? <p className="meta">No material risks flagged in the current analysis.</p> : null}
      </div>
    </section>
  );
}
