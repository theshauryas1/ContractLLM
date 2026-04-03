export default function DocumentLibrary({ documents }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Storage</p>
          <h2>Document Library</h2>
        </div>
        <span className="trace-chip">{documents?.length ?? 0} stored</span>
      </div>
      <div className="document-library">
        {(documents ?? []).map((item) => (
          <article key={item.id} className="document-card">
            <strong>{item.filename}</strong>
            <span className="meta">{item.kind} • {item.source_language} • {Math.round(item.size_bytes / 1024)} KB</span>
            <p>{item.extracted_text_preview || "No text extracted."}</p>
          </article>
        ))}
        {!documents?.length ? <p className="meta">No stored documents yet. Upload tender, company, or KB PDFs to reuse them across analyses.</p> : null}
      </div>
    </section>
  );
}
