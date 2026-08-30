import { formatCurrency, formatNumber, formatPercentage } from "./formatters.js";

export const severityLabels = {
  low: "Baixa",
  medium: "Média",
  high: "Alta",
  critical: "Crítica",
};

export function formatAlertMetric(metric) {
  if (metric.unit === "currency") return formatCurrency(metric.value);
  if (metric.unit === "percentage") return formatPercentage(metric.value, false);
  if (metric.unit === "percentage_change") return formatPercentage(metric.value);
  if (metric.unit === "percentage_points") {
    return `${formatPercentage(metric.value, false).replace("%", "")} p.p.`;
  }
  if (metric.unit === "score") return `${formatNumber(metric.value)}/100`;
  if (metric.unit === "count") return formatNumber(metric.value);
  return metric.value;
}
