import { CategoryScale, Chart as ChartJS, Legend, LinearScale, LineElement, PointElement, Tooltip } from "chart.js";
import { Line } from "react-chartjs-2";
import useChartPalette from "../../hooks/useChartPalette.js";
import { formatDate, formatPercentage } from "../../utils/formatters.js";
import SectionState from "../common/SectionState.jsx";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

export default function BranchDelayTrend({ points }) {
  const palette = useChartPalette();
  const hasData = points.some((point) => point.orders > 0);
  if (!hasData) return <section className="branch-trend"><div className="section-heading"><h2>Tendência de atrasos</h2></div><SectionState status="empty" title="Sem pedidos para traçar tendência" /></section>;
  const data = palette ? { labels: points.map((point) => formatDate(point.date)), datasets: [{ label: "Taxa de atraso", data: points.map((point) => point.orders ? point.delay_rate : null), borderColor: palette.warning, pointBackgroundColor: palette.warning, borderWidth: 2, pointRadius: points.length > 30 ? 0 : 2, tension: 0.2, spanGaps: true }] } : null;
  const options = palette ? { responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false }, tooltip: { backgroundColor: palette.tooltipBackground, titleColor: palette.tooltipText, bodyColor: palette.tooltipText, borderColor: palette.grid, borderWidth: 1, callbacks: { label: (context) => `Atrasos: ${formatPercentage(context.parsed.y, false)}` } } }, scales: { x: { grid: { display: false }, ticks: { color: palette.label, font: { family: palette.font }, maxTicksLimit: 8 } }, y: { min: 0, max: 100, grid: { color: palette.grid }, ticks: { color: palette.label, callback: (value) => `${value}%` } } } } : {};
  return <section className="branch-trend" aria-labelledby="branch-trend-title"><div className="section-heading"><h2 id="branch-trend-title">Tendência de atrasos</h2></div><p className="section-description">A taxa está melhorando ou piorando dentro do período?</p><div className="branch-trend-chart">{data && <Line data={data} options={options} role="img" aria-label="Taxa diária de atrasos da filial" />}</div></section>;
}
