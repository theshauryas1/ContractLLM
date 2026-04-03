const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api";
const DEFAULT_API_KEY = import.meta.env.VITE_API_KEY ?? "";

export function getStoredApiKey() {
  if (typeof window === "undefined") {
    return DEFAULT_API_KEY;
  }
  return window.localStorage.getItem("contractllm_api_key") ?? DEFAULT_API_KEY;
}

export function setStoredApiKey(value) {
  if (typeof window === "undefined") {
    return;
  }
  if (value) {
    window.localStorage.setItem("contractllm_api_key", value);
  } else {
    window.localStorage.removeItem("contractllm_api_key");
  }
}

function buildHeaders({ isFormData = false } = {}) {
  const headers = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  const apiKey = getStoredApiKey();
  if (apiKey) {
    headers["x-api-key"] = apiKey;
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
    const message = response.status === 401 ? "Unauthorized. Set the correct API key." : `Request failed: ${response.status}`;
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
