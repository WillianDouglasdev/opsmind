import { ArcElement, Chart as ChartJS, Tooltip } from "chart.js";
import { Doughnut, Pie } from "react-chartjs-2";
import { Link } from "react-router-dom";
import useChartPalette from "../../hooks/useChartPalette.js";
import { formatNumber, formatPercentage } from "../../utils/formatters.js";

ChartJS.register(ArcElement, Tooltip);

export default function DistributionChart({ segments, label, variant = "doughnut", totalLabel = "total" }) {
  const palette = useChartPalette();
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);
  if (!segments.length || total <= 0) return null;
  const describe = (segment) => `${segment.label}: ${formatNumber(segment.value)} · ${formatPercentage(segment.value / total * 100, false)}`;
  const color = (segment) => segment.category !== undefined
    ? palette?.categories[segment.category] : palette?.[segment.tone];
  const colorToken = (segment) => segment.category !== undefined
    ? `var(--chart-category-${segment.category + 1})` : `var(--chart-${segment.tone})`;
  const Chart = variant === "pie" ? Pie : Doughnut;
  const data = palette && {
    labels: segments.map((segment) => segment.label),
    datasets: [{ data: segments.map((segment) => segment.value), backgroundColor: segments.map(color), borderColor: palette.surface, borderWidth: 3, hoverOffset: 4 }],
  };
  const options = palette && {
    responsive: true, maintainAspectRatio: false, animation: false,
    ...(variant === "doughnut" ? { cutout: "76%" } : {}),
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: palette.tooltipBackground, titleColor: palette.tooltipText,
        bodyColor: palette.tooltipText, borderColor: palette.grid, borderWidth: 1,
        callbacks: { label: (context) => describe(segments[context.dataIndex]) },
      },
    },
  };
  return <div className={`distribution-chart ${variant}`}>
    <div className="distribution-plot">
      {data && <Chart data={data} options={options} role="img" aria-label={`${label}. ${segments.map(describe).join("; ")}`} />}
      {variant === "doughnut" && <div className="distribution-center" aria-hidden="true"><strong>{formatNumber(total)}</strong><span>{totalLabel}</span></div>}
    </div>
    <ul className="distribution-legend" aria-label={label}>
      {segments.map((segment) => <li key={segment.key} style={{ "--segment-color": colorToken(segment) }}>
        <i aria-hidden="true" />
        {segment.href ? <Link to={segment.href}>{segment.label}</Link> : <span>{segment.label}</span>}
        <strong>{formatNumber(segment.value)}</strong>
        <small>{formatPercentage(segment.value / total * 100, false)}</small>
      </li>)}
    </ul>
  </div>;
}
