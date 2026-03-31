const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api";

async function readJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export function fetchOverview() {
  return readJson("/reports/overview");
}

export function fetchRegressions() {
  return readJson("/reports/regressions");
}

export function fetchRuns() {
  return readJson("/reports/runs");
}
