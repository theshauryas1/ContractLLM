import { useMemo, useState } from "react";

export default function AnalysisForm({ documents, onSubmit, onUploadDocument, loading, uploadingKind }) {
  const [form, setForm] = useState({
    tenderTitle: "Municipal Services Tender",
    tenderText:
      "The bidder must provide ISO 9001 certification. The bidder shall demonstrate annual turnover above EUR 2 million. The bidder must comply with GDPR and provide evidence of three similar public-sector references.",
    companyProfileText:
      "Our company holds ISO 9001 certification, maintains GDPR controls, and delivered four public sector projects in the last three years. Annual turnover last year was EUR 2.4 million.",
    kbTitle: "Capability Notes",
    kbContent: "Public references include transport, utilities, and housing authority engagements.",
    targetLanguage: "auto",
    tenderDocumentId: "",
    companyDocumentId: "",
    knowledgeDocumentIds: [],
    tenderUpload: null,
    companyUpload: null,
    kbUpload: null
  });

  const groupedDocuments = useMemo(() => {
    const items = documents ?? [];
    return {
      tender: items.filter((item) => item.kind === "tender"),
      company: items.filter((item) => item.kind === "company"),
      knowledge_base: items.filter((item) => item.kind === "knowledge_base")
    };
  }, [documents]);

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleUpload(kind) {
    const file =
      kind === "tender"
        ? form.tenderUpload
        : kind === "company"
          ? form.companyUpload
          : form.kbUpload;

    if (!file) {
      return;
    }

    const uploaded = await onUploadDocument({ file, kind });
    if (kind === "tender") {
      setForm((current) => ({ ...current, tenderDocumentId: String(uploaded.id), tenderUpload: null, tenderText: "" }));
    } else if (kind === "company") {
      setForm((current) => ({ ...current, companyDocumentId: String(uploaded.id), companyUpload: null, companyProfileText: "" }));
    } else {
      setForm((current) => ({
        ...current,
        knowledgeDocumentIds: [...new Set([...current.knowledgeDocumentIds, String(uploaded.id)])],
        kbUpload: null
      }));
    }
  }

  function handleKnowledgeSelection(event) {
    const values = Array.from(event.target.selectedOptions).map((item) => item.value);
    updateField("knowledgeDocumentIds", values);
  }

  function handleSubmit(event) {
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
        : [],
      knowledge_document_ids: form.knowledgeDocumentIds.map((item) => Number(item))
    };

    if (form.tenderDocumentId) {
      payload.tender_document_id = Number(form.tenderDocumentId);
      payload.tender_text = "";
    }

    if (form.companyDocumentId) {
      payload.company_document_id = Number(form.companyDocumentId);
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

        <label className="field field-wide">
          <span>Tender Text</span>
          <textarea
            rows={6}
            value={form.tenderText}
            onChange={(event) => updateField("tenderText", event.target.value)}
            placeholder="Paste tender requirements here or select/upload a tender PDF below"
          />
        </label>

        <div className="field field-wide document-picker">
          <span>Tender PDF Storage</span>
          <div className="document-picker-row">
            <select value={form.tenderDocumentId} onChange={(event) => updateField("tenderDocumentId", event.target.value)}>
              <option value="">Use pasted tender text</option>
              {groupedDocuments.tender.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.filename} ({item.source_language})
                </option>
              ))}
            </select>
            <input type="file" accept=".pdf,.txt" onChange={(event) => updateField("tenderUpload", event.target.files?.[0] ?? null)} />
            <button type="button" className="secondary-button" disabled={!form.tenderUpload || uploadingKind === "tender"} onClick={() => handleUpload("tender")}>
              {uploadingKind === "tender" ? "Uploading..." : "Upload Tender PDF"}
            </button>
          </div>
        </div>

        <label className="field field-wide">
          <span>Company Profile</span>
          <textarea
            rows={6}
            value={form.companyProfileText}
            onChange={(event) => updateField("companyProfileText", event.target.value)}
            placeholder="Paste company capabilities or select/upload a stored company PDF"
          />
        </label>

        <div className="field field-wide document-picker">
          <span>Company Document Storage</span>
          <div className="document-picker-row">
            <select value={form.companyDocumentId} onChange={(event) => updateField("companyDocumentId", event.target.value)}>
              <option value="">Use pasted company profile text</option>
              {groupedDocuments.company.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.filename} ({item.source_language})
                </option>
              ))}
            </select>
            <input type="file" accept=".pdf,.txt" onChange={(event) => updateField("companyUpload", event.target.files?.[0] ?? null)} />
            <button type="button" className="secondary-button" disabled={!form.companyUpload || uploadingKind === "company"} onClick={() => handleUpload("company")}>
              {uploadingKind === "company" ? "Uploading..." : "Upload Company PDF"}
            </button>
          </div>
        </div>

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

        <div className="field field-wide document-picker">
          <span>Stored Knowledge Documents</span>
          <div className="document-picker-column">
            <select multiple value={form.knowledgeDocumentIds} onChange={handleKnowledgeSelection} className="multi-select">
              {groupedDocuments.knowledge_base.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.filename} ({item.source_language})
                </option>
              ))}
            </select>
            <div className="document-picker-row">
              <input type="file" accept=".pdf,.txt" onChange={(event) => updateField("kbUpload", event.target.files?.[0] ?? null)} />
              <button type="button" className="secondary-button" disabled={!form.kbUpload || uploadingKind === "knowledge_base"} onClick={() => handleUpload("knowledge_base")}>
                {uploadingKind === "knowledge_base" ? "Uploading..." : "Upload KB PDF"}
              </button>
            </div>
          </div>
        </div>

        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Analyzing..." : "Run Compliance Analysis"}
        </button>
      </form>
    </section>
  );
}
