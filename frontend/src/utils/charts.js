import { formatNumber, formatPercentage } from "./formatters.js";

const cssToken = (styles, name) => styles.getPropertyValue(name).trim();

export function readChartPalette(styles) {
  // Canvas não herda CSS. Todos os gráficos leem esta mesma tradução dos tokens semânticos.
  return {
    primary: cssToken(styles, "--chart-primary"),
    success: cssToken(styles, "--chart-success"),
    warning: cssToken(styles, "--chart-warning"),
    danger: cssToken(styles, "--chart-danger"),
    info: cssToken(styles, "--chart-info"),
    grid: cssToken(styles, "--chart-grid"),
    label: cssToken(styles, "--chart-label"),
    tooltipBackground: cssToken(styles, "--chart-tooltip-background"),
    tooltipText: cssToken(styles, "--chart-tooltip-text"),
    surface: cssToken(styles, "--surface"),
    categories: Array.from({ length: 5 }, (_, index) => cssToken(styles, `--chart-category-${index + 1}`)),
    font: cssToken(styles, "--font-body"),
  };
}

export function buildAlertSegments(alerts = []) {
  const severities = [
    ["critical", "Críticos", "danger"], ["high", "Altos", "warning"],
    ["medium", "Médios", "info"], ["low", "Baixos", "primary"],
  ];
  return severities.map(([key, label, tone]) => ({
    key, label, tone, value: alerts.filter((alert) => alert.severity === key).length,
  })).filter((segment) => segment.value > 0);
}

export function buildBranchDelaySegments(branches = []) {
  // Uma fatia representa uma contagem de pedidos, nunca a soma de taxas de filiais.
  // Incluímos todas as unidades: cortar o ranking mudaria o denominador da pizza.
  if (branches.some((branch) => !Number.isInteger(branch.delayed_orders) || branch.delayed_orders < 0)) return [];
  return [...branches].sort((left, right) => left.id - right.id).map((branch, index) => ({
    key: branch.id, label: branch.name, value: branch.delayed_orders, category: index % 5,
    href: `/operation/branches/${branch.id}?days=30&delivery=late`,
  })).filter((segment) => segment.value > 0);
}

export function buildQualitySegments(run) {
  const received = Number(run?.records_received ?? 0);
  if (received <= 0) return [];
  const valid = Number(run?.records_valid ?? 0);
  const rejected = Number(run?.records_rejected ?? 0);
  const validPercentage = Number.isFinite(Number(run?.quality_percentage))
    ? Number(run.quality_percentage)
    : valid / received * 100;
  return [
    { key: "valid", label: "Válidos", value: valid, percentage: validPercentage, tone: "success" },
    { key: "rejected", label: "Rejeitados", value: rejected, percentage: Math.max(0, 100 - validPercentage), tone: "danger" },
  ];
}

export function qualitySegmentLabel(segment) {
  return `${segment.label}: ${formatNumber(segment.value)} · ${formatPercentage(segment.percentage, false)}`;
}
