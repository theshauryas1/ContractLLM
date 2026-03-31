export default function FailureCard({ title, severity, detail, traceId, contract }) {
  return (
    <article className="failure-card">
      <div className={`severity severity-${severity}`}>{severity}</div>
      <h3>{title}</h3>
      {traceId ? <p className="meta">Trace {traceId}</p> : null}
      {contract ? <p className="meta">Contract {contract}</p> : null}
      <p>{detail}</p>
    </article>
  );
}
