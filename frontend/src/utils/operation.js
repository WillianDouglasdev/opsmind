export const operationPeriods = [7, 30, 90];

export function readOperationFilters(searchParams) {
  const requestedDays = Number(searchParams.get("days"));
  const requestedPage = Number(searchParams.get("page"));
  return {
    days: operationPeriods.includes(requestedDays) ? requestedDays : 30,
    branch: searchParams.get("branch") || "",
    status: searchParams.get("status") || "",
    delivery: searchParams.get("delivery") === "late" ? "late" : "all",
    page: Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1,
  };
}

export function operationSearchParams(filters, changes = {}) {
  // A query string preserva o contexto ao abrir uma filial e ao usar voltar/avançar.
  // Toda mudança de filtro retorna à primeira página para não produzir uma página vazia.
  const next = { ...filters, ...changes };
  if (!("page" in changes) && Object.keys(changes).length) next.page = 1;
  const params = new URLSearchParams();
  params.set("days", String(next.days));
  if (next.branch) params.set("branch", String(next.branch));
  if (next.status) params.set("status", next.status);
  if (next.delivery === "late") params.set("delivery", "late");
  if (next.page > 1) params.set("page", String(next.page));
  return params;
}

export function operationPath(path, filters, overrides = {}) {
  return `${path}?${operationSearchParams(filters, overrides).toString()}`;
}

export function branchRows(overview) {
  if (!overview?.branches) return [];
  return [...overview.branches].sort((left, right) => {
    if (!left.health && right.health) return 1;
    if (left.health && !right.health) return -1;
    return right.delay_rate - left.delay_rate || left.name.localeCompare(right.name, "pt-BR");
  });
}
