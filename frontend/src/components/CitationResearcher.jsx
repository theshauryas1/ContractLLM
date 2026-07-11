import { useState } from "react";
import { submitCopilotSearchCitations } from "../api";

export default function CitationResearcher() {
  const [keywords, setKeywords] = useState("");
  const [results, setResults] = useState("");
  const [loading, setLoading] = useState(false);

  const sampleSearches = [
    "GDPR consent requirements Supreme Court",
    "Breach of contract damages calculation precedent",
    "Non-compete clause enforceability employment law",
    "Liability cap limitation commercial dispute"
  ];

  async function handleSearch(searchTerm) {
    const term = searchTerm || keywords;
    if (!term.trim()) return;

    setLoading(true);
    setResults("");
    try {
      const response = await submitCopilotSearchCitations({ keywords: term });
      setResults(response.results);
    } catch (e) {
      setResults(`Error searching case citations: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>Legal Case & Citation Researcher</h2>
          <p className="meta">Query landmark rulings, precedents, and court citations</p>
        </div>
      </div>

      <div className="search-bar-wrapper" style={{ marginTop: "24px" }}>
        <div className="input-row">
          <input
            type="text"
            placeholder="Search keywords (e.g. 'unilateral contract revocation', 'ISO 9001 liability')..."
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            disabled={loading}
          />
          <button className="primary-button" onClick={() => handleSearch()} disabled={loading}>
            {loading ? "Searching..." : "Search Precedents"}
          </button>
        </div>
      </div>

      <div style={{ marginTop: "16px" }}>
        <p className="meta" style={{ marginBottom: "8px" }}>Suggested Search Queries:</p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {sampleSearches.map((s, idx) => (
            <button
              key={idx}
              className="badge-btn"
              onClick={() => {
                setKeywords(s);
                handleSearch(s);
              }}
              disabled={loading}
              style={{
                background: "var(--accent-soft)",
                color: "var(--accent)",
                border: "0",
                borderRadius: "16px",
                padding: "6px 12px",
                fontSize: "0.8rem",
                cursor: "pointer"
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {results && (
        <div className="search-output-panel" style={{ marginTop: "28px" }}>
          <h3>Search Results & Precedents</h3>
          <div className="results-content-wrapper" style={{ marginTop: "14px" }}>
            <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontFamily: "monospace", fontSize: "0.9rem", lineHeight: "1.5" }}>
              {results}
            </pre>
          </div>
        </div>
      )}
    </section>
  );
}
