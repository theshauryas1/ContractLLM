import { useState } from "react";

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? "");
      resolve(result.includes(",") ? result.split(",")[1] : result);
    };
    reader.onerror = () => reject(new Error("Failed to read file."));
    reader.readAsDataURL(file);
  });
}

export default function AnalysisForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    tenderTitle: "Municipal Services Tender",
    tenderText:
      "The bidder must provide ISO 9001 certification. The bidder shall demonstrate annual turnover above EUR 2 million. The bidder must comply with GDPR and provide evidence of three similar public-sector references.",
    companyProfileText:
      "Our company holds ISO 9001 certification, maintains GDPR controls, and delivered four public sector projects in the last three years. Annual turnover last year was EUR 2.4 million.",
    kbTitle: "Capability Notes",
    kbContent: "Public references include transport, utilities, and housing authority engagements.",
    targetLanguage: "auto",
    tenderFile: null,
    companyFile: null
  });

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const payload = {
      tender_title: form.tenderTitle,
      tender_text: form.tenderText,
      company_profile_text: form.companyProfileText,
      target_language: form.targetLanguage,
      kb_documents: form.kbContent
        ? [
            {
              title: form.kbTitle || "Knowledge Base Note",
              content: form.kbContent
            }
          ]
        : []
    };

    if (form.tenderFile) {
      payload.tender_document_base64 = await fileToBase64(form.tenderFile);
      payload.tender_text = "";
    }

    if (form.companyFile) {
      payload.company_document_base64 = await fileToBase64(form.companyFile);
      payload.company_profile_text = "";
    }

    onSubmit(payload);
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Tender Intake</p>
          <h2>Analyze A Tender</h2>
        </div>
        <span className="trace-chip">{loading ? "Running" : "Ready"}</span>
      </div>
      <form className="analysis-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Tender Title</span>
          <input
            value={form.tenderTitle}
            onChange={(event) => updateField("tenderTitle", event.target.value)}
            placeholder="Public-sector maintenance framework"
          />
        </label>
        <label className="field field-wide">
          <span>Tender Text</span>
          <textarea
            rows={6}
            value={form.tenderText}
            onChange={(event) => updateField("tenderText", event.target.value)}
            placeholder="Paste tender requirements here"
          />
        </label>
        <label className="field">
          <span>Tender PDF</span>
          <input type="file" accept=".pdf,.txt" onChange={(event) => updateField("tenderFile", event.target.files?.[0] ?? null)} />
        </label>
        <label className="field field-wide">
          <span>Company Profile</span>
          <textarea
            rows={6}
            value={form.companyProfileText}
            onChange={(event) => updateField("companyProfileText", event.target.value)}
            placeholder="Paste company capabilities, certifications, and references"
          />
        </label>
        <label className="field">
          <span>Company PDF</span>
          <input type="file" accept=".pdf,.txt" onChange={(event) => updateField("companyFile", event.target.files?.[0] ?? null)} />
        </label>
        <label className="field">
          <span>Output Language</span>
          <select value={form.targetLanguage} onChange={(event) => updateField("targetLanguage", event.target.value)}>
            <option value="auto">Auto match tender</option>
            <option value="en">English</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="es">Spanish</option>
            <option value="nl">Dutch</option>
          </select>
        </label>
        <label className="field">
          <span>KB Note Title</span>
          <input value={form.kbTitle} onChange={(event) => updateField("kbTitle", event.target.value)} />
        </label>
        <label className="field field-wide">
          <span>Additional Knowledge Note</span>
          <textarea
            rows={4}
            value={form.kbContent}
            onChange={(event) => updateField("kbContent", event.target.value)}
            placeholder="Optional internal evidence or policy note"
          />
        </label>
        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Analyzing..." : "Run Compliance Analysis"}
        </button>
      </form>
    </section>
  );
}
