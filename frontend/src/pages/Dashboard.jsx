import { useEffect, useState } from "react";
import {
  fetchAnalyses,
  fetchAnalysis,
  fetchDocuments,
  fetchOverview,
  submitAnalysis,
  submitFeedback,
  uploadDocument
} from "../api";
import AnalysisForm from "../components/AnalysisForm";
import AuthPanel from "../components/AuthPanel";
import ComplianceMatrix from "../components/ComplianceMatrix";
import DocumentLibrary from "../components/DocumentLibrary";
import OverviewPanel from "../components/OverviewPanel";
import RiskPanel from "../components/RiskPanel";

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadingKind, setUploadingKind] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadDashboard() {
    const [overviewData, analysesData, documentsData] = await Promise.all([fetchOverview(), fetchAnalyses(), fetchDocuments()]);
    setOverview(overviewData);
    setAnalyses(analysesData.analyses);
    setDocuments(documentsData.items);
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

  async function handleUploadDocument({ file, kind }) {
    setUploadingKind(kind);
    setError("");
    setMessage("");
    try {
      const uploaded = await uploadDocument({ file, kind });
      await loadDashboard();
      setMessage(`${uploaded.filename} uploaded and stored.`);
      return uploaded;
    } catch (uploadError) {
      setError(uploadError.message);
      throw uploadError;
    } finally {
      setUploadingKind("");
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

      <AuthPanel onSaved={loadDashboard} />
      <OverviewPanel overview={overview} analyses={analyses} onSelectAnalysis={handleSelectAnalysis} />
      <AnalysisForm
        documents={documents}
        onSubmit={handleSubmit}
        onUploadDocument={handleUploadDocument}
        loading={loading}
        uploadingKind={uploadingKind}
      />
      <DocumentLibrary documents={documents} />

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
