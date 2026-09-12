import { useState } from "react";
import { CategoryScale, Chart as ChartJS, Legend, LinearScale, LineElement, PointElement, Tooltip } from "chart.js";
import { Line } from "react-chartjs-2";
import { formatPercentage } from "../../utils/formatters.js";
import useChartPalette from "../../hooks/useChartPalette.js";
import SectionState from "../common/SectionState.jsx";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

export default function TrendChart({ trend, status, onRetry }) {
  const [showTable, setShowTable] = useState(false);
  const palette = useChartPalette();

  const hasData = trend?.series.some((point) => point.total_orders > 0);
  // Mês sem pedidos elegíveis vira lacuna visual, não 0% de desempenho.
  // O eixo completo também evita esconder taxas menores que as da demo.
  const data = trend && palette ? {
    labels: trend.series.map((point) => point.label),
    datasets: [
      { label: "Entregas no prazo", data: trend.series.map((point) => point.total_orders > 0 ? point.value : null), borderColor: palette.primary, pointBackgroundColor: palette.primary, borderWidth: 2, pointRadius: 3, tension: 0.2, spanGaps: false },
      { label: "Meta", data: trend.series.map(() => trend.target), borderColor: palette.label, borderDash: [4, 5], borderWidth: 1, pointRadius: 0 },
    ],
  } : null;
  const options = palette ? {
    responsive: true, maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: { backgroundColor: palette.tooltipBackground, titleColor: palette.tooltipText, bodyColor: palette.tooltipText, borderColor: palette.grid, borderWidth: 1, padding: 12, cornerRadius: 4, callbacks: { label: (context) => context.dataset.label + ": " + formatPercentage(context.parsed.y, false) } },
    },
    scales: {
      x: { border: { display: false }, grid: { display: false }, ticks: { color: palette.label, font: { family: palette.font, size: 11 } } },
      y: { min: 0, max: 100, border: { display: false }, grid: { color: palette.grid, drawTicks: false }, ticks: { stepSize: 25, color: palette.label, padding: 10, font: { family: palette.font, size: 11 }, callback: (value) => value + "%" } },
    },
  } : {};

  return (
    <section className="trend-section" aria-labelledby="trend-title">
      <div className="section-heading"><h2 id="trend-title">Entregas no prazo</h2>{hasData && <button type="button" className="text-button" aria-expanded={showTable} aria-controls="trend-data-table" onClick={() => setShowTable((value) => !value)}>{showTable ? "Ocultar dados" : "Ver dados"}</button>}</div>
      <p className="section-description">Como as entregas evoluíram nos últimos seis meses.</p>
      {status !== "success" ? <SectionState status={status} onRetry={onRetry} />
        : !hasData ? <SectionState status="empty" title="Sem histórico para comparar" description="Não há pedidos elegíveis nos meses retornados." />
          : <>
            <div className="chart-legend"><span><i />Entregas no prazo</span><span><i className="target" />Meta {formatPercentage(trend.target, false)}</span></div>
            <div className="chart-container">{data && <Line data={data} options={options} role="img" aria-label="Evolução mensal de entregas no prazo. Use Ver dados para consultar valores em tabela." />}</div>
            <div className="trend-table-wrap" id="trend-data-table" hidden={!showTable}><table><caption>Entregas no prazo por mês · meta de {formatPercentage(trend.target, false)}</caption><thead><tr><th scope="col">Mês</th><th scope="col">No prazo</th><th scope="col">Pedidos elegíveis</th></tr></thead><tbody>{trend.series.map((point) => <tr key={point.month}><th scope="row">{point.month}</th><td>{point.total_orders > 0 ? formatPercentage(point.value, false) : "Sem base"}</td><td>{point.total_orders}</td></tr>)}</tbody></table></div>
          </>}
    </section>
  );
}
