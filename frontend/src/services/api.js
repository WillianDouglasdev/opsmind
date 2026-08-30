const API_URL = (
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? "" : "http://127.0.0.1:8000")
).replace(/\/$/, "");

// As páginas conhecem apenas funções de domínio; detalhes de URL e erro ficam centralizados aqui.
async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { Accept: "application/json", ...options.headers },
  });

  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    const error = new Error(
      data?.detail || `A API respondeu com o status ${response.status}.`,
    );
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return response.json();
}

export function getHealth(options) {
  return request("/api/health/", options);
}

export function getDashboardSummary(options) {
  return request("/api/dashboard/summary/", options);
}

export function getDashboardTrends(options) {
  return request("/api/dashboard/trends/", options);
}

export function getDashboardChanges(options) {
  return request("/api/dashboard/changes/", options);
}

export function getAlerts(options) {
  return request("/api/alerts/", options);
}

export function getAlertInvestigation(alertKey, options) {
  return request(`/api/alerts/${encodeURIComponent(alertKey)}/investigation/`, options);
}

export function getAlertRecommendations(alertKey, options) {
  return request(`/api/alerts/${encodeURIComponent(alertKey)}/recommendations/`, options);
}

export function getActions(options) {
  return request("/api/actions/", options);
}

export function createAction(alertKey, recommendationKey, options = {}) {
  return request("/api/actions/", {
    ...options,
    method: "POST",
    headers: { "Content-Type": "application/json", ...options.headers },
    body: JSON.stringify({
      alert_key: alertKey,
      recommendation_key: recommendationKey,
    }),
  });
}

export function updateActionStatus(id, status, options = {}) {
  return request(`/api/actions/${encodeURIComponent(id)}/`, {
    ...options,
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...options.headers },
    body: JSON.stringify({ status }),
  });
}

export function askAssistant(question, options = {}) {
  return request("/api/assistant/query/", {
    ...options,
    method: "POST",
    headers: { "Content-Type": "application/json", ...options.headers },
    body: JSON.stringify({ question }),
  });
}

export function getExecutiveSummary(options = {}) {
  return request("/api/assistant/executive-summary/", {
    ...options,
    method: "POST",
    headers: { "Content-Type": "application/json", ...options.headers },
    body: JSON.stringify({}),
  });
}
