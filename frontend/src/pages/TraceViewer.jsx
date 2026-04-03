import { useState } from "react";
import TraceDiff from "../components/TraceDiff";

export default function TraceViewer({ run }) {
  const [view, setView] = useState("output");
  const [inputLanguageView, setInputLanguageView] = useState("source");
  const [outputLanguageView, setOutputLanguageView] = useState("source");

  if (!run) {
    return (
      <section className="panel">
        <h2>Trace Viewer</h2>
        <p>No trace runs yet. Ingest a trace to inspect prompt outcomes and contract failures.</p>
      </section>
    );
  }

  const trace = run.input_payload ?? {};
  const translatedTrace = run.results?.translated_trace;
  const language = run.results?.source_language || trace.metadata?.language || "en";
  const wasTranslated = Boolean(translatedTrace || trace.metadata?.translated || trace.metadata?.source_language);
  const canSwitchLanguage = Boolean(translatedTrace);
  const viewOptions = [
    { id: "output", label: "Output" },
    { id: "translation", label: "Translation" },
    { id: "failures", label: "Failures" },
    { id: "repairs", label: "Repairs" }
  ];
  const sideContent =
    view === "translation"
      ? translatedTrace
      : view === "failures"
      ? run.results?.failures
      : view === "repairs"
      ? run.results?.suggested_repairs
        : trace.output;

  const inputText = inputLanguageView === "en" ? translatedTrace?.input_text ?? trace.input_text : trace.input_text;
  const outputText = outputLanguageView === "en" ? translatedTrace?.output ?? trace.output : trace.output;
  const contextText = inputLanguageView === "en" ? translatedTrace?.context ?? trace.context : trace.context;

  return (
    <section className="panel">
      <div className="trace-viewer-header">
        <div>
          <h2>Trace Viewer</h2>
          <p className="meta">Trace {run.trace_id}</p>
        </div>
        <div className="trace-badges">
          <span className="trace-chip">Prompt {run.prompt_version}</span>
          <span className="trace-chip">Language {language}</span>
          {wasTranslated ? <span className="trace-chip trace-chip-accent">Multilingual</span> : null}
        </div>
      </div>
      <div className="trace-toolbar">
        {viewOptions.map((option) => (
          <button
            key={option.id}
            type="button"
            className={`trace-option ${view === option.id ? "trace-option-active" : ""}`}
            onClick={() => setView(option.id)}
          >
            {option.label}
          </button>
        ))}
      </div>
      {canSwitchLanguage ? (
        <div className="language-controls">
          <label className="language-field">
            <span className="meta">Input Language</span>
            <select value={inputLanguageView} onChange={(event) => setInputLanguageView(event.target.value)}>
              <option value="source">Original ({language})</option>
              <option value="en">English</option>
            </select>
          </label>
          <label className="language-field">
            <span className="meta">Output Language</span>
            <select value={outputLanguageView} onChange={(event) => setOutputLanguageView(event.target.value)}>
              <option value="source">Original ({language})</option>
              <option value="en">English</option>
            </select>
          </label>
        </div>
      ) : null}
      <TraceDiff
        inputText={view === "translation" ? translatedTrace?.input_text ?? inputText : inputText}
        outputText={view === "translation" ? translatedTrace?.output ?? outputText : outputText}
        context={view === "translation" ? translatedTrace?.context ?? contextText : contextText}
        metadata={trace.metadata}
        inputLanguageLabel={inputLanguageView === "en" ? "English" : `Original (${language})`}
        outputLanguageLabel={outputLanguageView === "en" ? "English" : `Original (${language})`}
        sideTitle={view}
        sideContent={sideContent}
      />
    </section>
  );
}
