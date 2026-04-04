const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api";

const API_KEY = import.meta.env.VITE_API_KEY ?? "local-dev-key";

function buildHeaders({ isFormData = false } = {}) {
  const headers = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (API_KEY) {
    headers["x-api-key"] = API_KEY;
  }
  return headers;
}

async function readJson(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...buildHeaders({ isFormData }),
      ...(options.headers ?? {})
    }
  });

  if (!response.ok) {
    const message = response.status === 401 ? "Unauthorized." : `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return response.json();
}

export function fetchOverview() {
  return readJson("/overview");
}

export function fetchAnalyses() {
  return readJson("/analyses");
}

export function fetchDocuments() {
  return readJson("/documents");
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

export function uploadDocument({ file, kind }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("kind", kind);
  return readJson("/documents", {
    method: "POST",
    body: formData
  });
}
