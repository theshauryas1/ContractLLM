export default function TraceDiff({ before, after }) {
  return (
    <div className="trace-diff">
      <div>
        <h3>Before</h3>
        <pre>{before}</pre>
      </div>
      <div>
        <h3>After</h3>
        <pre>{after}</pre>
      </div>
    </div>
  );
}
