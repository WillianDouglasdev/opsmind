import { ArcElement, Chart as ChartJS, Tooltip } from "chart.js";
import { Doughnut } from "react-chartjs-2";
import useChartPalette from "../../hooks/useChartPalette.js";
import { buildQualitySegments, qualitySegmentLabel } from "../../utils/charts.js";
import { formatPercentage } from "../../utils/formatters.js";

ChartJS.register(ArcElement, Tooltip);

export default function DataQualityDonut({ run, compact = false }) {
  const palette = useChartPalette();
  const segments = buildQualitySegments(run);
  if (!segments.length) return null;
  const quality = run.quality_percentage;
  const toneColors = palette ? { success: palette.success, danger: palette.danger } : {};
  const data = palette ? {
    labels: segments.map((segment) => segment.label),
    datasets: [{
      data: segments.map((segment) => segment.value),
      backgroundColor: segments.map((segment) => toneColors[segment.tone]),
      borderColor: palette.surface,
      borderWidth: compact ? 2 : 3,
      hoverOffset: 3,
    }],
  } : null;
  const options = palette ? {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "70%",
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: palette.tooltipBackground,
        titleColor: palette.tooltipText,
        bodyColor: palette.tooltipText,
        borderColor: palette.grid,
        borderWidth: 1,
        callbacks: { label: (context) => qualitySegmentLabel(segments[context.dataIndex]) },
      },
    },
  } : {};

  return (
    <div className={`quality-donut${compact ? " compact" : ""}`}>
      <div className="quality-donut-plot">
        {data && <Doughnut data={data} options={options} role="img" aria-label={`Qualidade da pipeline: ${segments.map(qualitySegmentLabel).join("; ")}`} />}
        <div className="quality-donut-center" aria-hidden="true"><strong>{formatPercentage(quality, false)}</strong><span>qualidade</span></div>
      </div>
      <ul className="quality-donut-legend" aria-label="Distribuição da qualidade">
        {segments.map((segment) => <li className={segment.tone} key={segment.key}><i aria-hidden="true" /><span>{segment.label}</span><strong>{segment.value}</strong><small>{formatPercentage(segment.percentage, false)}</small></li>)}
      </ul>
    </div>
  );
}
