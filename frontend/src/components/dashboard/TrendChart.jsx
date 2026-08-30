import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { MoreHorizontal } from "lucide-react";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
);

const options = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index", intersect: false },
  plugins: {
    legend: {
      align: "end",
      labels: {
        usePointStyle: true,
        pointStyle: "circle",
        boxWidth: 7,
        boxHeight: 7,
        color: "#64748b",
        font: { family: "Inter", size: 11 },
      },
    },
    tooltip: {
      backgroundColor: "#152235",
      padding: 12,
      cornerRadius: 8,
      titleFont: { family: "Inter", weight: 600 },
      bodyFont: { family: "Inter" },
      callbacks: { label: (context) => `${context.dataset.label}: ${context.parsed.y}%` },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      border: { display: false },
      ticks: { color: "#8491a3", font: { family: "Inter", size: 11 } },
    },
    y: {
      min: 60,
      max: 100,
      border: { display: false },
      grid: { color: "rgba(148, 163, 184, 0.16)" },
      ticks: {
        stepSize: 10,
        color: "#8491a3",
        font: { family: "Inter", size: 11 },
        callback: (value) => `${value}%`,
      },
    },
  },
};

function TrendChart({ trend, loading }) {
  const data = trend ? {
    labels: trend.series.map((point) => point.label),
    datasets: [
      {
        label: "Entregas no prazo",
        data: trend.series.map((point) => point.value),
        borderColor: "#137f8b",
        backgroundColor: "rgba(19, 127, 139, 0.12)",
        borderWidth: 2.5,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: "#ffffff",
        pointBorderWidth: 2,
        fill: true,
        tension: 0.35,
      },
      {
        label: "Meta",
        data: trend.series.map(() => trend.target),
        borderColor: "#b4bdc9",
        borderDash: [5, 5],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
    ],
  } : null;

  return (
    <article className="panel chart-card">
      <div className="panel-heading chart-heading">
        <div>
          <h2>Desempenho Operacional</h2>
          <p>Entregas no prazo nos últimos 6 meses</p>
        </div>
        <button className="icon-button" type="button" aria-label="Opções do gráfico">
          <MoreHorizontal size={19} />
        </button>
      </div>
      <div className="chart-container">
        {data
          ? <Line options={options} data={data} />
          : <div className="data-placeholder">{loading ? "Carregando histórico..." : "Histórico indisponível."}</div>}
      </div>
    </article>
  );
}

export default TrendChart;
