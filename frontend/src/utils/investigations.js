const ALLOWED_DAYS = new Set([7, 30, 90]);

export function readInvestigationFilters(searchParams) {
  const parsedDays = Number(searchParams.get("days"));
  const parsedBranch = Number(searchParams.get("branch"));
  return {
    days: ALLOWED_DAYS.has(parsedDays) ? parsedDays : 30,
    branch: Number.isInteger(parsedBranch) && parsedBranch > 0 ? String(parsedBranch) : "",
  };
}

export function investigationSearchParams(filters, changes = {}) {
  const next = { ...filters, ...changes };
  const params = new URLSearchParams();
  params.set("days", String(ALLOWED_DAYS.has(Number(next.days)) ? next.days : 30));
  if (next.branch) params.set("branch", String(next.branch));
  return params;
}

export function investigationPath(filters, changes = {}) {
  return `/investigations/delivery-delays?${investigationSearchParams(filters, changes)}`;
}
