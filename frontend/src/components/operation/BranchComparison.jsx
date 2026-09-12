import { formatCurrency, formatNumber, formatPercentage } from "../../utils/formatters.js";

function valueFor(value, unit) {
  if (value === null || value === undefined) return "Sem base";
  if (unit === "currency") return formatCurrency(value);
  if (unit === "percentage") return formatPercentage(value, false);
  return formatNumber(value);
}

export default function BranchComparison({ comparisons, scope }) {
  return <section className="branch-comparison" aria-labelledby="comparison-title"><div className="section-heading"><h2 id="comparison-title">Filial × média</h2></div><p className="section-description">{scope}</p><div className="comparison-list">{comparisons.map((item) => <div key={item.key}><span>{item.label}</span><strong>{valueFor(item.branch_value, item.unit)}</strong><small>média {valueFor(item.average_value, item.unit)}</small><em className={item.difference > 0 && item.key === "delay_rate" ? "metric-worse" : ""}>{item.difference === null ? "sem comparação" : `${item.difference > 0 ? "+" : ""}${valueFor(item.difference, item.unit)}`}</em></div>)}</div></section>;
}
