import { useEffect, useState } from "react";
import { fetchAnalyses, fetchAnalysis, fetchOverview, submitAnalysis, submitFeedback } from "../api";
import AnalysisForm from "../components/AnalysisForm";
import ComplianceMatrix from "../components/ComplianceMatrix";
import OverviewPanel from "../components/OverviewPanel";
import RiskPanel from "../components/RiskPanel";

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadDashboard() {
    const [overviewData, analysesData] = await Promise.all([fetchOverview(), fetchAnalyses()]);
    setOverview(overviewData);
    setAnalyses(analysesData.analyses);
  }

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        await loadDashboard();
      } catch (_) {
        if (mounted) {
          setError("Backend not reachable yet. Start FastAPI and check your API key configuration.");
        }
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, []);

  async function handleSubmit(payload) {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const analysis = await submitAnalysis(payload);
      setCurrentAnalysis(analysis);
      await loadDashboard();
      setMessage("Compliance matrix updated.");
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectAnalysis(analysisId) {
    setError("");
    try {
      const analysis = await fetchAnalysis(analysisId);
      setCurrentAnalysis(analysis);
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  async function handleFeedback(payload) {
    setError("");
    setMessage("");
    try {
      await submitFeedback(payload);
      setMessage("Feedback stored. The next similar requirement will use this signal.");
      await loadDashboard();
      if (currentAnalysis?.analysis_id) {
        setCurrentAnalysis(await fetchAnalysis(currentAnalysis.analysis_id));
      }
    } catch (feedbackError) {
      setError(feedbackError.message);
    }
  }

  return (
    <main className="layout">
      <section className="hero">
        <p className="eyebrow">Agentic Compliance System</p>
        <h1>Tender reasoning, grounded evidence, and auditable risk analysis.</h1>
        <p className="lede">
          Parse multilingual tenders, retrieve company evidence, classify compliance gaps, and capture reviewer feedback
          in one workflow.
        </p>
      </section>

      <OverviewPanel overview={overview} analyses={analyses} onSelectAnalysis={handleSelectAnalysis} />
      <AnalysisForm onSubmit={handleSubmit} loading={loading} />

      {message ? (
        <section className="panel panel-message">
          <p>{message}</p>
        </section>
      ) : null}

      {error ? (
        <section className="panel panel-error">
          <p>{error}</p>
        </section>
      ) : null}

      <ComplianceMatrix analysis={currentAnalysis} onSubmitFeedback={handleFeedback} />
      <RiskPanel risks={currentAnalysis?.matrix?.risks ?? []} />
    </main>
  );
}
