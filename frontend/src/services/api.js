// Em produção, a ausência de VITE_API_URL usa /api na mesma origem (rewrite da Vercel).
// Em projetos separados, configure a URL pública da API no build e o CORS no backend.
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
    // Preservamos status e payload: a investigação usa 404 e a criação de ação usa
    // 409 para informar que a recomendação já está no plano. Não converta erros em [].
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

function operationQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  });
  return query.toString();
}

export function getOperationOverview(days = 30, options) {
  return request(`/api/operation/overview/?${operationQuery({ days })}`, options);
}

export function getOperationDelays(days = 30, options) {
  return request(`/api/operation/delays/?${operationQuery({ days })}`, options);
}

export function getOperationBranch(branchId, days = 30, options) {
  return request(`/api/operation/branches/${encodeURIComponent(branchId)}/?${operationQuery({ days })}`, options);
}

export function getOperationOrders(params, options) {
  return request(`/api/operation/orders/?${operationQuery(params)}`, options);
}

export function getPipelines(options) {
  return request("/api/data/pipelines/", options);
}

export function getPipeline(pipelineKey, options) {
  return request(`/api/data/pipelines/${encodeURIComponent(pipelineKey)}/`, options);
}

export function getPipelineRun(pipelineKey, runId, options) {
  return request(`/api/data/pipelines/${encodeURIComponent(pipelineKey)}/runs/${encodeURIComponent(runId)}/`, options);
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
