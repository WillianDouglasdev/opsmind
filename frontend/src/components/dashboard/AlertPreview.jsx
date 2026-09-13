import { ArrowRight, ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import { formatAlertMetric, severityLabels } from "../../utils/alerts.js";
import SectionState from "../common/SectionState.jsx";
import DistributionChart from "../charts/DistributionChart.jsx";
import { buildAlertSegments } from "../../utils/charts.js";

export default function AlertPreview({ section, onRetry }) {
  const alerts = section.data ?? [];
  const leading = alerts[0];
  // A cor tem função: âmbar para atenção, vermelho somente se houver alerta crítico.
  // Ausência de resposta é erro; ausência de alertas após sucesso é um estado distinto.
  const tone = section.status !== "success" ? "unavailable"
    : alerts.length === 0 ? "clear"
      : alerts.some((alert) => alert.severity === "critical") ? "critical" : "attention";
  return (
    <section className={"attention-panel " + tone} aria-labelledby="attention-title">
      <div className="attention-heading"><h2 id="attention-title">Precisa de atenção</h2><ArrowUpRight size={20} aria-hidden="true" /></div>
      {section.status !== "success" ? <SectionState status={section.status} onRetry={onRetry} />
        : alerts.length === 0
          ? <><strong className="attention-number">0</strong><p className="attention-copy">Nenhum alerta ativo.</p><p>As regras atuais não apontam situações para investigar.</p></>
          : <>
            <DistributionChart segments={buildAlertSegments(alerts)} label="Alertas por severidade" totalLabel="alertas ativos" />
            <Link className="attention-leading" to={"/alerts/" + leading.key}><span>Prioridade {severityLabels[leading.severity].toLowerCase()}</span>{leading.title}</Link>
            {leading.metrics?.[0] && <p className="attention-evidence">{formatAlertMetric(leading.metrics[0])} {leading.metrics[0].label.toLowerCase()}</p>}
          </>}
      <Link className="attention-link" to="/alerts">Ver prioridades <ArrowRight size={17} aria-hidden="true" /></Link>
    </section>
  );
}
