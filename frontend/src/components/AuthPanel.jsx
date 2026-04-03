import { useEffect, useState } from "react";
import { getStoredApiKey, setStoredApiKey } from "../api";

export default function AuthPanel({ onSaved }) {
  const [value, setValue] = useState("");

  useEffect(() => {
    setValue(getStoredApiKey());
  }, []);

  function handleSubmit(event) {
    event.preventDefault();
    setStoredApiKey(value.trim());
    onSaved?.();
  }

  return (
    <section className="panel auth-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Auth</p>
          <h2>Backend API Key</h2>
        </div>
        <span className="trace-chip">{value ? "Configured" : "Optional in local dev"}</span>
      </div>
      <form className="auth-form" onSubmit={handleSubmit}>
        <input
          type="password"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Paste x-api-key for protected backend routes"
        />
        <button type="submit" className="secondary-button">Save Key</button>
      </form>
      <p className="meta">Stored in your browser and sent as the `x-api-key` header on API requests.</p>
    </section>
  );
}
