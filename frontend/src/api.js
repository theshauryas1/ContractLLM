const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

function buildHeaders() {
  const headers = { "Content-Type": "application/json" };
  if (API_KEY) {
    headers["x-api-key"] = API_KEY;
  }
  return headers;
}

async function readJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...buildHeaders(),
      ...(options.headers ?? {})
    }
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export function fetchOverview() {
  return readJson("/overview");
}

export function fetchAnalyses() {
  return readJson("/analyses");
}

export function fetchAnalysis(analysisId) {
  return readJson(`/analyses/${analysisId}`);
}

export function submitAnalysis(payload) {
  return readJson("/analyze", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function submitFeedback(payload) {
  return readJson("/feedback", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
