function formatBlock(value) {
  if (value === undefined || value === null || value === "") {
    return "Not available.";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

const viewLabels = {
  output: "Output",
  translation: "Translation",
  failures: "Failures",
  repairs: "Repairs"
};

export default function TraceDiff({
  inputText,
  outputText,
  context,
  metadata,
  inputLanguageLabel,
  outputLanguageLabel,
  sideTitle,
  sideContent
}) {
  const model = metadata?.model;

  return (
    <div className="trace-diff">
      <div className="trace-panel trace-panel-input">
        <div className="trace-panel-header">
          <h3>Input</h3>
          <div className="trace-badges">
            {model ? <span className="trace-chip">{model}</span> : null}
            {inputLanguageLabel ? <span className="trace-chip">{inputLanguageLabel}</span> : null}
          </div>
        </div>
        <pre>{formatBlock(inputText)}</pre>
        <div className="trace-context">
          <span className="meta">Context</span>
          <pre>{formatBlock(context)}</pre>
        </div>
      </div>
      <div className="trace-panel trace-panel-output">
        <div className="trace-panel-header">
          <h3>{viewLabels[sideTitle] ?? "Output"}</h3>
          {outputLanguageLabel && sideTitle === "output" ? (
            <span className="trace-chip">{outputLanguageLabel}</span>
          ) : null}
        </div>
        <pre>{formatBlock(sideContent ?? outputText)}</pre>
      </div>
    </div>
  );
}
