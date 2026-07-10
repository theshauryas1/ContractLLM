import { useState, useEffect } from "react";
import { fetchUserProfile, updateUserProfile } from "../api";

export default function UserProfilePanel() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [fullName, setFullName] = useState("");
  const [preferredLanguage, setPreferredLanguage] = useState("en");
  const [country, setCountry] = useState("");
  const [state, setState] = useState("");
  const [timezone, setTimezone] = useState("");
  const [legalProfession, setLegalProfession] = useState("");
  const [industry, setIndustry] = useState("");
  const [defaultJurisdiction, setDefaultJurisdiction] = useState("");
  const [preferredAiModel, setPreferredAiModel] = useState("gemini-3.5-flash");

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await fetchUserProfile();
        setProfile(data);
        setFullName(data.full_name ?? "");
        setPreferredLanguage(data.preferred_language ?? "en");
        setCountry(data.country ?? "");
        setState(data.state ?? "");
        setTimezone(data.timezone ?? "");
        setLegalProfession(data.legal_profession ?? "");
        setIndustry(data.industry ?? "");
        setDefaultJurisdiction(data.default_jurisdiction ?? "");
        setPreferredAiModel(data.preferred_ai_model ?? "gemini-3.5-flash");
      } catch (err) {
        setError("Failed to load user profile details.");
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const updated = await updateUserProfile({
        full_name: fullName || null,
        preferred_language: preferredLanguage,
        country: country || null,
        state: state || null,
        timezone: timezone || null,
        legal_profession: legalProfession || null,
        industry: industry || null,
        default_jurisdiction: defaultJurisdiction || null,
        preferred_ai_model: preferredAiModel || null,
      });
      setProfile(updated);
      setSuccess("Profile preferences saved successfully.");
    } catch (err) {
      setError("Failed to save profile changes.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="panel">
        <p>Loading profile preferences...</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>User Profile & Preferences</h2>
      <p className="lede">Customize your AI Legal Copilot experience and active workspace defaults.</p>

      {error ? <p style={{ color: "var(--danger)", margin: "12px 0" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--accent)", margin: "12px 0", fontWeight: "bold" }}>{success}</p> : null}

      <form onSubmit={handleSave} className="form-grid">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <div>
            <label htmlFor="full-name" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Full Name</label>
            <input
              id="full-name"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Sarah Jenkins"
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            />
          </div>

          <div>
            <label htmlFor="pref-lang" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Preferred Language</label>
            <select
              id="pref-lang"
              value={preferredLanguage}
              onChange={(e) => setPreferredLanguage(e.target.value)}
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            >
              <option value="en">English (US/UK)</option>
              <option value="hi">Hindi (India)</option>
              <option value="de">German (Germany)</option>
              <option value="fr">French (France)</option>
              <option value="es">Spanish (Spain)</option>
              <option value="ar">Arabic (UAE)</option>
              <option value="ja">Japanese (Japan)</option>
            </select>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px", marginTop: "16px" }}>
          <div>
            <label htmlFor="country" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Country</label>
            <input
              id="country"
              type="text"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              placeholder="e.g. USA"
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            />
          </div>

          <div>
            <label htmlFor="state" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>State / Province</label>
            <input
              id="state"
              type="text"
              value={state}
              onChange={(e) => setState(e.target.value)}
              placeholder="e.g. California"
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            />
          </div>

          <div>
            <label htmlFor="timezone" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Timezone</label>
            <input
              id="timezone"
              type="text"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              placeholder="e.g. America/Los_Angeles"
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "16px" }}>
          <div>
            <label htmlFor="legal-prof" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Legal Profession</label>
            <input
              id="legal-prof"
              type="text"
              value={legalProfession}
              onChange={(e) => setLegalProfession(e.target.value)}
              placeholder="e.g. Compliance Officer, Legal Counsel"
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            />
          </div>

          <div>
            <label htmlFor="industry" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Industry Sector</label>
            <input
              id="industry"
              type="text"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              placeholder="e.g. FinTech, Procurement, Healthcare"
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "16px" }}>
          <div>
            <label htmlFor="def-jurisdiction" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Default Jurisdiction</label>
            <input
              id="def-jurisdiction"
              type="text"
              value={defaultJurisdiction}
              onChange={(e) => setDefaultJurisdiction(e.target.value)}
              placeholder="e.g. US-CA, EU-DE, IN-DL"
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            />
          </div>

          <div>
            <label htmlFor="pref-ai" style={{ display: "block", marginBottom: "6px", fontWeight: "bold" }}>Preferred AI Model</label>
            <select
              id="pref-ai"
              value={preferredAiModel}
              onChange={(e) => setPreferredAiModel(e.target.value)}
              style={{ width: "100%", padding: "10px", borderRadius: "12px", border: "1px solid rgba(23, 32, 36, 0.15)" }}
            >
              <option value="gemini-3.5-flash">Google Gemini 3.5 Flash (Recommended)</option>
              <option value="grok-4.20-reasoning">xAI Grok Reasoning</option>
              <option value="gpt-4o">OpenAI GPT-4o</option>
              <option value="claude-3-5-sonnet">Anthropic Claude 3.5 Sonnet</option>
              <option value="mistral-large">Mistral Large</option>
              <option value="ollama-local">Local model (Ollama / vLLM)</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          style={{
            marginTop: "20px",
            padding: "12px 24px",
            border: "none",
            borderRadius: "16px",
            background: "var(--accent)",
            color: "white",
            fontWeight: "bold",
            cursor: "pointer"
          }}
        >
          {saving ? "Saving changes..." : "Save Preferences"}
        </button>
      </form>
    </section>
  );
}
