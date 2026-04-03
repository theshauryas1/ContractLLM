import { useState } from "react";

function confidenceLabel(value) {
  return `${Math.round((value ?? 0) * 100)}% confidence`;
}

export default function ComplianceMatrix({ analysis, onSubmitFeedback }) {
  const [drafts, setDrafts] = useState({});

  if (!analysis) {
    return (
      <section className="panel">
        <h2>Compliance Matrix</h2>
        <p className="meta">Run an analysis to review requirement coverage, evidence, and risk.</p>
      </section>
    );
  }

  function updateDraft(requirementId, patch) {
    setDrafts((current) => ({
      ...current,
      [requirementId]: {
        corrected_status: patch.corrected_status ?? current[requirementId]?.corrected_status ?? "",
        comments: patch.comments ?? current[requirementId]?.comments ?? ""
      }
    }));
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Compliance Agent</p>
          <h2>{analysis.tender_title}</h2>
        </div>
        <div className="trace-badges">
          <span className="trace-chip">Tender {analysis.tender_language}</span>
          <span className="trace-chip">Output {analysis.output_language}</span>
          <span className="trace-chip">Provider {analysis.provider}</span>
          <span className="trace-chip">RAG {analysis.retrieval_backend}</span>
          <span className="trace-chip">Reasoning {analysis.reasoning_backend}</span>
        </div>
      </div>
      <p className="lede compact">{analysis.matrix.executive_summary}</p>
      <div className="matrix-summary">
        <span className="trace-chip">Full {analysis.matrix.summary.full_count}</span>
        <span className="trace-chip">Partial {analysis.matrix.summary.partial_count}</span>
        <span className="trace-chip">Missing {analysis.matrix.summary.missing_count}</span>
        <span className="trace-chip">Review {analysis.matrix.summary.review_required_count}</span>
      </div>
      <div className="matrix-grid">
        {analysis.matrix.rows.map((row) => {
          const draft = drafts[row.requirement_id] ?? { corrected_status: "", comments: "" };
          return (
            <article key={row.requirement_id} className="matrix-card">
              <div className="matrix-card-header">
                <div>
                  <p className="meta">{row.requirement_id} • {row.category_label}</p>
                  <h3>{row.requirement_text}</h3>
                </div>
                <div className="trace-badges">
                  <span className={`status-pill status-${row.status}`}>{row.status_label}</span>
                  <span className="trace-chip">{confidenceLabel(row.confidence)}</span>
                </div>
              </div>
              <p>{row.reasoning}</p>
              <p className="meta">{row.recommended_action}</p>
              <div className="evidence-list">
                {row.evidence.map((item) => (
                  <div key={`${row.requirement_id}-${item.source}`} className="evidence-item">
                    <strong>{item.source}</strong>
                    <p>{item.snippet}</p>
                    <span className="meta">Score {item.score}</span>
                  </div>
                ))}
                {!row.evidence.length ? <p className="meta">No supporting evidence retrieved.</p> : null}
              </div>
              {row.feedback_examples.length ? (
                <div className="feedback-signal">
                  {row.feedback_examples.map((item, index) => (
                    <span key={`${row.requirement_id}-feedback-${index}`} className="trace-chip trace-chip-accent">
                      Feedback {item.corrected_status} ({Math.round(item.similarity * 100)}%)
                    </span>
                  ))}
                </div>
              ) : null}
              <div className="feedback-form">
                <select
                  value={draft.corrected_status}
                  onChange={(event) => updateDraft(row.requirement_id, { corrected_status: event.target.value })}
                >
                  <option value="">Add reviewer feedback</option>
                  <option value="full">Full</option>
                  <option value="partial">Partial</option>
                  <option value="missing">Missing</option>
                </select>
                <input
                  value={draft.comments}
                  onChange={(event) => updateDraft(row.requirement_id, { comments: event.target.value })}
                  placeholder="Reviewer comment"
                />
                <button
                  type="button"
                  className="secondary-button"
                  disabled={!draft.corrected_status}
                  onClick={() =>
                    onSubmitFeedback({
                      analysis_id: analysis.analysis_id,
                      requirement_id: row.requirement_id,
                      requirement_text: row.requirement_text,
                      original_status: row.status,
                      corrected_status: draft.corrected_status,
                      comments: draft.comments
                    })
                  }
                >
                  Save Feedback
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
