import { useCallback } from "react";
import { AlertTriangle, ArrowLeft, Scale } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import SectionState from "../components/common/SectionState.jsx";
import InvestigationEvidence from "../components/investigations/InvestigationEvidence.jsx";
import InvestigationNextSteps from "../components/investigations/InvestigationNextSteps.jsx";
import InvestigationTimeline from "../components/investigations/InvestigationTimeline.jsx";
import PeriodSelector from "../components/operation/PeriodSelector.jsx";
import useApiResource from "../hooks/useApiResource.js";
import { getDeliveryDelayInvestigation } from "../services/api.js";
import { formatAlertMetric, severityLabels } from "../utils/alerts.js";
import { formatCurrency, formatNumber, formatPercentage } from "../utils/formatters.js";
import {
  investigationSearchParams,
  readInvestigationFilters,
} from "../utils/investigations.js";

export function DeliveryDelayInvestigation({ state, filters, onPeriodChange }) {
  if (state.status !== "success") {
    const title = state.status === "loading" ? "Organizando as evidências…"
      : state.error?.status === 404 ? "Filial não encontrada"
        : "Não foi possível carregar a investigação";
    return <SectionState status={state.status} title={title} onRetry={state.retry} />;
  }
  const data = state.data;
  if (data.data_status === "empty") {
    return <div className="investigation-workspace"><div className="investigations-toolbar"><Link className="text-button" to={data.navigation.investigations_url}><ArrowLeft size={14} aria-hidden="true" /> Investigações</Link><PeriodSelector value={filters.days} onChange={onPeriodChange} /></div><SectionState status="empty" title="Nenhum atraso para investigar" description={data.causality_notice} /></div>;
  }
  const summary = data.summary;
  return (
    <div className="investigation-workspace">
      <div className="investigations-toolbar"><Link className="text-button" to={data.navigation.investigations_url}><ArrowLeft size={14} aria-hidden="true" /> Investigações</Link><PeriodSelector value={filters.days} onChange={onPeriodChange} /></div>
      <nav className="investigation-breadcrumb" aria-label="Navegação estrutural"><Link to={data.navigation.investigations_url}>Investigações</Link><span>/</span><span>Atrasos de entrega</span></nav>
      <header className={`investigation-opening ${summary.severity}`}>
        <div><p className="eyebrow">Investigação · {data.period.days} dias</p><span className={`severity-badge ${summary.severity}`}>{severityLabels[summary.severity]}</span><h2>{summary.title}</h2><p>{summary.situation}</p></div>
        <dl className="investigation-opening-summary"><div><dt>Filial</dt><dd>{summary.branch.name}</dd></div><div><dt>Taxa de atraso</dt><dd>{formatPercentage(summary.branch_delay_rate, false)}</dd></div><div><dt>Operação</dt><dd>{formatPercentage(summary.operation_delay_rate, false)}</dd></div><div><dt>Diferença</dt><dd>{formatAlertMetric({ value: summary.difference_percentage_points, unit: "percentage_points" })}</dd></div></dl>
      </header>
      <section className="investigation-impact" aria-label="Resumo do impacto"><div><span>Pedidos atrasados</span><strong>{formatNumber(summary.delayed_orders)}</strong></div><div><span>Clientes afetados</span><strong>{formatNumber(summary.impacted_customers)}</strong></div><div><span>Valor relacionado</span><strong>{formatCurrency(summary.affected_revenue)}</strong></div><div><span>Período anterior</span><strong>{formatPercentage(summary.previous_delay_rate, false)}</strong></div></section>
      {data.data_status === "partial" && <div className="investigation-partial" role="status"><AlertTriangle size={17} aria-hidden="true" /><p><strong>Dados incompletos.</strong> A investigação possui o sinal principal, mas não encontrou evidências adicionais.</p></div>}
      <div className="causality-notice"><Scale size={20} aria-hidden="true" /><div><strong>Correlação não é causalidade</strong><p>{data.causality_notice}</p></div></div>
      <InvestigationEvidence evidence={data.evidence} />
      <InvestigationTimeline timeline={data.timeline} />
      <InvestigationNextSteps steps={data.next_steps} />
    </div>
  );
}

export default function DeliveryDelayInvestigationPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = readInvestigationFilters(searchParams);
  const loader = useCallback(
    (options) => getDeliveryDelayInvestigation({ days: filters.days, branch: filters.branch }, options),
    [filters.days, filters.branch],
  );
  const state = useApiResource(loader);
  const changePeriod = (days) => setSearchParams(investigationSearchParams(filters, { days }));
  return <DeliveryDelayInvestigation state={state} filters={filters} onPeriodChange={changePeriod} />;
}
