import { useEffect, useState } from "react";
import { fetchOverview, fetchRegressions, fetchRuns } from "../api";
import Contracts from "./Contracts";
import TraceViewer from "./TraceViewer";
import FailureCard from "../components/FailureCard";
import PassRateChart from "../components/PassRateChart";

const defaultContracts = [
  {
    id: "context_faithfulness",
    type: "semantic",
    description: "Response must stay grounded in the provided context."
  },
  {
    id: "no_pii",
    type: "pattern",
    description: "Output must not leak personally identifiable information."
  },
  {
    id: "response_format",
    type: "structural",
    description: "Output must be valid JSON."
  },
  {
    id: "rag_support",
    type: "rag_grounding",
    description: "Output claims should be supported by retrieved knowledge base evidence."
  }
];

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [regressions, setRegressions] = useState([]);
  const [runs, setRuns] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const [overviewData, regressionData, runsData] = await Promise.all([
          fetchOverview(),
          fetchRegressions(),
          fetchRuns()
        ]);
        if (!mounted) {
          return;
        }
        setOverview(overviewData);
        setRegressions(
          regressionData.points.map((point, index) => ({
            name: `Run ${index + 1}`,
            passRate: point.pass_rate
          }))
        );
        setRuns(runsData.runs);
      } catch (loadError) {
        if (!mounted) {
          return;
        }
        setError("Backend not reachable yet. Start FastAPI to see live evaluation data.");
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, []);

  const failures =
    overview?.recent_failures?.map((failure) => ({
      title: failure.failure_type.replaceAll("_", " "),
      severity: failure.severity,
      detail: failure.rationale,
      traceId: failure.trace_id,
      contract: failure.contract
    })) ?? [];

  return (
    <main className="layout">
      <section className="hero">
        <p className="eyebrow">Contract-driven LLM validation</p>
        <h1>Regression tracking and failure diagnostics for production prompts.</h1>
        <p className="lede">
          Validate traces against structural, pattern, semantic, and optional RAG-grounding contracts.
        </p>
      </section>
      <section className="stats-grid">
        <article className="stat-card">
          <span>Total Runs</span>
          <strong>{overview?.total_runs ?? 0}</strong>
        </article>
        <article className="stat-card">
          <span>Average Pass Rate</span>
          <strong>{Math.round((overview?.average_pass_rate ?? 0) * 100)}%</strong>
        </article>
        <article className="stat-card">
          <span>Latest Pass Rate</span>
          <strong>{Math.round((overview?.latest_pass_rate ?? 0) * 100)}%</strong>
        </article>
        <article className="stat-card">
          <span>Failing Runs</span>
          <strong>{overview?.failing_runs ?? 0}</strong>
        </article>
      </section>
      <section className="panel">
        <div className="panel-header">
          <h2>Pass Rate Trend</h2>
        </div>
        <PassRateChart data={regressions} />
      </section>
      {error ? (
        <section className="panel">
          <h2>Connection</h2>
          <p>{error}</p>
        </section>
      ) : null}
      <section className="grid">
        {failures.map((failure) => (
          <FailureCard key={failure.title} {...failure} />
        ))}
      </section>
      <Contracts contracts={defaultContracts} />
      <TraceViewer run={runs[0]} />
    </main>
  );
}
