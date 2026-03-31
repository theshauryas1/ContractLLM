import TraceDiff from "../components/TraceDiff";

export default function TraceViewer({ run }) {
  if (!run) {
    return (
      <section className="panel">
        <h2>Trace Viewer</h2>
        <p>No trace runs yet. Ingest a trace to inspect prompt outcomes and contract failures.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Trace Viewer</h2>
      <p className="meta">Trace {run.trace_id}</p>
      <TraceDiff before={JSON.stringify(run.results, null, 2)} after={JSON.stringify(run.results.failures, null, 2)} />
    </section>
  );
}
