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
import ComplianceMatrix from "../components/ComplianceMatrix";
import DocumentLibrary from "../components/DocumentLibrary";
import OverviewPanel from "../components/OverviewPanel";
import RiskPanel from "../components/RiskPanel";
import UserProfilePanel from "../components/UserProfilePanel";
import CopilotChat from "../components/CopilotChat";
import DocumentDrafter from "../components/DocumentDrafter";
import CitationResearcher from "../components/CitationResearcher";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("compliance");
  const [overview, setOverview] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadingKind, setUploadingKind] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadDashboard() {
    const [overviewData, analysesData, documentsData] = await Promise.all([
      fetchOverview(),
      fetchAnalyses(),
      fetchDocuments()
    ]);
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
          setError("Backend not reachable yet. Check that the deployed frontend points to the deployed API.");
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
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-logo">⚖️</span>
          <h2>Legal Copilot</h2>
        </div>
        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeTab === "compliance" ? "active" : ""}`}
            onClick={() => setActiveTab("compliance")}
          >
            📋 Compliance Engine
          </button>
          <button
            className={`nav-item ${activeTab === "chat" ? "active" : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            💬 AI Legal Chat
          </button>
          <button
            className={`nav-item ${activeTab === "drafter" ? "active" : ""}`}
            onClick={() => setActiveTab("drafter")}
          >
            ✍️ Document Drafter
          </button>
          <button
            className={`nav-item ${activeTab === "research" ? "active" : ""}`}
            onClick={() => setActiveTab("research")}
          >
            🔍 Citation Research
          </button>
          <button
            className={`nav-item ${activeTab === "profile" ? "active" : ""}`}
            onClick={() => setActiveTab("profile")}
          >
            👤 User Profile
          </button>
        </nav>
      </aside>

      <main className="content-area">
        <section className="hero">
          <p className="eyebrow">AI Legal Intelligence Platform</p>
          <h1>Your AI Legal Copilot for Contracts, Compliance, Legal Research, and Governance</h1>
          <p className="lede">
            Draft contracts, analyze vendor compliance matrices, search legal citations, and ask our chatbot legal questions.
          </p>
        </section>

        {message && (
          <section className="panel panel-message">
            <p>{message}</p>
          </section>
        )}

        {error && (
          <section className="panel panel-error">
            <p>{error}</p>
          </section>
        )}

        {activeTab === "compliance" && (
          <>
            <OverviewPanel overview={overview} analyses={analyses} onSelectAnalysis={handleSelectAnalysis} />
            <AnalysisForm
              documents={documents}
              onSubmit={handleSubmit}
              onUploadDocument={handleUploadDocument}
              loading={loading}
              uploadingKind={uploadingKind}
            />
            <DocumentLibrary documents={documents} />
            <ComplianceMatrix analysis={currentAnalysis} onSubmitFeedback={handleFeedback} />
            <RiskPanel risks={currentAnalysis?.matrix?.risks ?? []} />
          </>
        )}

        {activeTab === "chat" && <CopilotChat />}

        {activeTab === "drafter" && <DocumentDrafter />}

        {activeTab === "research" && <CitationResearcher />}

        {activeTab === "profile" && <UserProfilePanel />}
      </main>
    </div>
  );
}
