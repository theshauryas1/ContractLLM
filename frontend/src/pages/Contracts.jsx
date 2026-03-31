export default function Contracts({ contracts }) {
  return (
    <section className="panel">
      <h2>Contracts</h2>
      <p>Author YAML rules that map each quality requirement to a dedicated evaluator.</p>
      <div className="contract-list">
        {contracts.map((contract) => (
          <article key={contract.id} className="contract-item">
            <h3>{contract.id}</h3>
            <p>{contract.description}</p>
            <span>{contract.type}</span>
          </article>
        ))}
      </div>
    </section>
  );
}
