import { useState } from "react";
import { submitCopilotDraft } from "../api";

export default function DocumentDrafter() {
  const [templateName, setTemplateName] = useState("Mutual Non-Disclosure Agreement (NDA)");
  const [partyDetails, setPartyDetails] = useState("");
  const [customTerms, setCustomTerms] = useState("");
  const [draftResult, setDraftResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const templates = [
    // Startup Templates
    "Mutual Non-Disclosure Agreement (NDA)",
    "Co-Founder Equity & Vesting Agreement",
    "Shareholder Agreement",
    "ESOP Grant Letter Template",
    "SaaS Terms of Service & SLA",
    "Privacy Policy (GDPR / CCPA)",
    "Freelancer Consultancy Agreement",
    // Individual Templates
    "Rental Agreement Review Notice",
    "Consumer Rights Refund Complaint Notice",
    "Self-Proved Last Will and Testament",
    "Formal Breach of Contract Notice",
    // SME Templates
    "Standard Vendor Services Agreement",
    "Corporate Risk Mitigation Policy",
    "Internal Information Security Policy"
  ];

  async function handleDraft() {
    if (!partyDetails.trim()) {
      alert("Please provide the party names and essential details.");
      return;
    }
    setLoading(true);
    setDraftResult("");
    setCopied(false);
    try {
      const response = await submitCopilotDraft({
        template_name: templateName,
        party_details: partyDetails,
        custom_terms: customTerms
      });
      setDraftResult(response.draft);
    } catch (e) {
      setDraftResult(`Error generating contract: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(draftResult);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>AI Document Drafter</h2>
          <p className="meta">Generate instant, high-fidelity legal drafts and agreements</p>
        </div>
      </div>

      <div className="analysis-form" style={{ marginTop: "24px" }}>
        <div className="field">
          <label>Select Drafting Template</label>
          <select value={templateName} onChange={(e) => setTemplateName(e.target.value)}>
            {templates.map((t, idx) => (
              <option key={idx} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Custom parameters / Clauses</label>
          <input
            type="text"
            placeholder="e.g. 5 years duration, governing law Delaware, no intellectual property transfer..."
            value={customTerms}
            onChange={(e) => setCustomTerms(e.target.value)}
          />
        </div>

        <div className="field field-wide">
          <label>Party Names & Essential Details</label>
          <textarea
            rows="4"
            placeholder="Enter contracting party names, addresses, business scope, or specific values (e.g. Acme Corp and Beta Inc, 10% equity split, vest over 4 years)..."
            value={partyDetails}
            onChange={(e) => setPartyDetails(e.target.value)}
          />
        </div>

        <div className="field field-wide">
          <button className="primary-button" onClick={handleDraft} disabled={loading}>
            {loading ? "Drafting Agreement..." : "Generate Custom Draft"}
          </button>
        </div>
      </div>

      {draftResult && (
        <div className="draft-output-panel" style={{ marginTop: "28px" }}>
          <div className="output-header" style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", alignItems: "center" }}>
            <h3>Generated Draft</h3>
            <button className="secondary-button" onClick={handleCopy}>
              {copied ? "Copied!" : "Copy to Clipboard"}
            </button>
          </div>
          <div className="draft-content-wrapper">
            <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontFamily: "monospace", fontSize: "0.9rem", lineHeight: "1.5" }}>
              {draftResult}
            </pre>
          </div>
        </div>
      )}
    </section>
  );
}
