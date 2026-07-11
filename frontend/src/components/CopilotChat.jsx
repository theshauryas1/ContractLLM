import { useState, useRef, useEffect } from "react";
import { submitCopilotChat } from "../api";

export default function CopilotChat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hello! I am your AI Legal Copilot. Ask me to draft agreements, review clauses, explain complex policies, or draft legal notices."
    }
  ]);
  const [input, setInput] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState("Individual");
  const chatEndRef = useRef(null);

  const personaSuggestions = {
    Individual: [
      { label: "Rental Review", text: "Please review my rental agreement draft and highlight major tenant liabilities." },
      { label: "Draft Will", text: "Draft a basic self-proved last will and testament template for an individual with two heirs." },
      { label: "Consumer Complaint", text: "Draft a consumer complaint notice to an e-commerce platform for failing to refund a defective item." },
      { label: "Explain Loan Terms", text: "Explain the common hidden charges or standard terms in a personal loan agreement." }
    ],
    Startup: [
      { label: "Draft NDA", text: "Draft a mutual non-disclosure agreement (NDA) for two software companies sharing proprietary source code." },
      { label: "Founder Agreement", text: "Draft a simple founder agreement outlining equity split, vesting schedule, and IP assignment." },
      { label: "SaaS Terms", text: "Draft the core sections of a SaaS Terms of Service covering service levels, billing, and liability caps." },
      { label: "Privacy Policy", text: "Generate a GDPR-compliant privacy policy outline for a mobile application collecting email and location data." }
    ],
    "SME & Enterprise": [
      { label: "Vendor Compliance", text: "What are the standard vendor compliance requirements and SLAs we should enforce for an IT service provider?" },
      { label: "Procurement Review", text: "Explain what key risks to search for during a procurement contract review." },
      { label: "Draft Risk Policy", text: "Provide a template for an enterprise risk management policy covering business continuity and data breaches." }
    ],
    "Law Firm": [
      { label: "Case Summarization", text: "Provide a template structure for summarizing court cases including facts, issue, ruling, and ratio decidendi." },
      { label: "Drafting Notice", text: "Draft a formal legal notice for breach of contract due to failure to deliver services on time." },
      { label: "Draft Settlement", text: "Draft a mutual release and settlement agreement to resolve a commercial dispute between two firms." }
    ]
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(textToSend) {
    const msg = textToSend || input;
    if (!msg.trim()) return;

    const userMsg = { role: "user", content: msg };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await submitCopilotChat({ message: msg, context: context });
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${e.message}. Please check API connection.` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>AI Chat Copilot</h2>
          <p className="meta">Your interactive legal research, drafting, and analysis partner</p>
        </div>
      </div>

      {/* Suggestion tabs */}
      <div className="persona-selector">
        {Object.keys(personaSuggestions).map((persona) => (
          <button
            key={persona}
            className={`tab-btn ${selectedPersona === persona ? "active" : ""}`}
            onClick={() => setSelectedPersona(persona)}
          >
            {persona}
          </button>
        ))}
      </div>

      <div className="suggestions-grid">
        {personaSuggestions[selectedPersona].map((suggestion, idx) => (
          <button
            key={idx}
            className="suggestion-card"
            onClick={() => handleSend(suggestion.text)}
            disabled={loading}
          >
            <strong>{suggestion.label}</strong>
            <span>{suggestion.text.substring(0, 50)}...</span>
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="chat-container">
        <div className="messages-list">
          {messages.map((m, idx) => (
            <div key={idx} className={`message-bubble ${m.role}`}>
              <div className="bubble-sender">{m.role === "user" ? "You" : "Legal Copilot"}</div>
              <div className="bubble-content">{m.content}</div>
            </div>
          ))}
          {loading && (
            <div className="message-bubble assistant loading">
              <div className="bubble-sender">Legal Copilot</div>
              <div className="bubble-content">Analyzing legal parameters...</div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Inputs */}
      <div className="chat-input-area">
        <div className="field" style={{ marginBottom: "12px" }}>
          <label>Optional Context / Document Text</label>
          <textarea
            rows="2"
            placeholder="Paste contract terms, background facts, or policy text to ground the assistant's reasoning..."
            value={context}
            onChange={(e) => setContext(e.target.value)}
          />
        </div>
        <div className="input-row">
          <input
            type="text"
            placeholder="Ask a legal question, request a clause, or draft a notice..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={loading}
          />
          <button className="primary-button" onClick={() => handleSend()} disabled={loading}>
            Send
          </button>
        </div>
      </div>
    </section>
  );
}
