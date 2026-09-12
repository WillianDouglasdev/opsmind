import { useCallback } from "react";
import { ArrowRight } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import PeriodSelector from "../components/operation/PeriodSelector.jsx";
import SectionState from "../components/common/SectionState.jsx";
import useApiResource from "../hooks/useApiResource.js";
import { getOperationDelays } from "../services/api.js";
import { formatNumber, formatPercentage } from "../utils/formatters.js";
import { operationPath, operationSearchParams, readOperationFilters } from "../utils/operation.js";
import { investigationPath } from "../utils/investigations.js";

export default function OperationDelaysPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = readOperationFilters(searchParams);
  const loader = useCallback((options) => getOperationDelays(filters.days, options), [filters.days]);
  const state = useApiResource(loader);
  if (state.status !== "success") return <SectionState status={state.status} title={state.status === "loading" ? "Abrindo os atrasos…" : undefined} onRetry={state.retry} />;
  const { metrics, branches, period } = state.data;
  return <div className="delay-page">
    <div className="operation-toolbar"><Link className="text-button" to={operationPath("/operation", filters, { branch: "", delivery: "all" })}>← Voltar para Operação</Link><PeriodSelector value={filters.days} onChange={(days) => setSearchParams((current) => operationSearchParams(readOperationFilters(current), { days }))} /></div>
    <section className="delay-opening" aria-labelledby="delay-opening-title"><div><p className="eyebrow">{period.days} dias · status do pedido</p><h2 id="delay-opening-title">{formatPercentage(metrics.delay_rate, false)} de atraso</h2><p>{formatNumber(metrics.delayed_orders)} de {formatNumber(metrics.orders)} pedidos · {formatNumber(metrics.impacted_customers)} clientes afetados.</p><small>Definição: <code>{state.data.metric_definition.rule}</code>. Atraso não é inferido por datas.</small></div>{metrics.delayed_orders > 0 && <Link className="primary-link" to={investigationPath({ days: filters.days, branch: "" })}>Investigar evidências <ArrowRight size={14} aria-hidden="true" /></Link>}</section>
    <section className="delay-ranking" aria-labelledby="delay-ranking-title"><div className="section-heading"><div><h2 id="delay-ranking-title">Contribuição por filial</h2><p className="section-description">Onde se concentram os pedidos classificados como atrasados.</p></div></div>{metrics.delayed_orders === 0 ? <SectionState status="empty" title="Nenhum pedido atrasado neste período" description="As filiais continuam acessíveis na visão geral da Operação." /> : <ol>{branches.filter((branch) => branch.delayed_orders > 0).map((branch) => <li key={branch.id}><div><span>{branch.name}</span><strong>{formatPercentage(branch.delay_rate, false)}</strong></div><div className="delay-contribution-track" role="img" aria-label={`${branch.name}: ${formatPercentage(branch.contribution_percentage, false)} dos atrasos`}><span style={{ width: `${branch.contribution_percentage}%` }} /></div><p>{formatNumber(branch.delayed_orders)} atrasados · {formatPercentage(branch.contribution_percentage, false)} do total</p><Link aria-label={`Abrir ${branch.name} filtrada por atrasos`} to={operationPath(`/operation/branches/${branch.id}`, filters, { branch: "", delivery: "late" })}>Ver filial <ArrowRight size={14} aria-hidden="true" /></Link></li>)}</ol>}</section>
  </div>;
}
