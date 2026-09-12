import { useCallback } from "react";
import { AlertTriangle, ArrowRight, Boxes, UsersRound } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import BranchTable from "../components/operation/BranchTable.jsx";
import OperationMetrics from "../components/operation/OperationMetrics.jsx";
import OrderFilters from "../components/operation/OrderFilters.jsx";
import OrderTable from "../components/operation/OrderTable.jsx";
import PeriodSelector from "../components/operation/PeriodSelector.jsx";
import SectionState from "../components/common/SectionState.jsx";
import useApiResource from "../hooks/useApiResource.js";
import { getOperationOrders, getOperationOverview } from "../services/api.js";
import { formatNumber, formatPercentage } from "../utils/formatters.js";
import { operationPath, operationSearchParams, readOperationFilters } from "../utils/operation.js";

export function OperationOverview({ state, filters, onPeriodChange }) {
  if (state.status !== "success") return <SectionState status={state.status} title={state.status === "loading" ? "Organizando a visão da operação…" : undefined} onRetry={state.retry} />;
  const overview = state.data;
  const worst = overview.attention.worst_branch;
  return <>
    <div className="operation-toolbar"><p>De {overview.period.start_date.split("-").reverse().join("/")} a {overview.period.end_date.split("-").reverse().join("/")}</p><PeriodSelector value={filters.days} onChange={onPeriodChange} /></div>
    <OperationMetrics metrics={overview.metrics} />
    <section className="operation-branches" aria-labelledby="operation-branches-title"><div className="section-heading"><div><h2 id="operation-branches-title">Filiais</h2><p className="section-description">Compare volume, atrasos, receita e sinais operacionais.</p></div><Link className="text-button" to={operationPath("/operation/delays", filters, { branch: "", status: "", delivery: "all" })}>Explorar atrasos <ArrowRight size={14} aria-hidden="true" /></Link></div>{overview.branches.length ? <BranchTable overview={overview} filters={filters} /> : <SectionState status="empty" title="Nenhuma filial cadastrada" />}</section>
    <section className="operation-attention" aria-labelledby="operation-attention-title"><div className="section-heading"><h2 id="operation-attention-title">Pontos de atenção</h2></div><div className="attention-layout">
      <article className="attention-branch"><AlertTriangle size={18} aria-hidden="true" /><span>Maior taxa com base</span>{worst ? <><strong>{worst.name}</strong><p>{formatPercentage(worst.delay_rate, false)} · {formatNumber(worst.delayed_orders)} pedidos atrasados</p><Link to={operationPath(`/operation/branches/${worst.id}`, filters, { branch: "", delivery: "late" })}>Abrir filial <ArrowRight size={14} aria-hidden="true" /></Link></> : <p>Nenhuma filial possui pedidos no período.</p>}</article>
      <article><Boxes size={18} aria-hidden="true" /><span>Estoque crítico</span>{overview.attention.critical_products.length ? <ul>{overview.attention.critical_products.map((product) => <li key={product.sku}><strong>{product.sku}</strong><p>{product.name} · déficit de {formatNumber(product.deficit)} unidades em {formatNumber(product.affected_branches)} filial(is)</p></li>)}</ul> : <p>Nenhuma combinação está abaixo do mínimo.</p>}</article>
      <article><UsersRound size={18} aria-hidden="true" /><span>Clientes estratégicos</span><strong>{formatNumber(overview.attention.strategic_customers_impacted)}</strong><p>afetados por pedidos atrasados no período.</p></article>
    </div></section>
  </>;
}

export default function OperationPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = readOperationFilters(searchParams);
  const loadOverview = useCallback((options) => getOperationOverview(filters.days, options), [filters.days]);
  const loadOrders = useCallback((options) => getOperationOrders({ days: filters.days, branch: filters.branch, status: filters.status, delivery: filters.delivery, page: filters.page, page_size: 15 }, options), [filters.days, filters.branch, filters.status, filters.delivery, filters.page]);
  const overviewState = useApiResource(loadOverview);
  const ordersState = useApiResource(loadOrders);
  const changeFilters = (changes) => setSearchParams((current) => operationSearchParams(readOperationFilters(current), changes));

  return <div className="operation-page">
    <OperationOverview state={overviewState} filters={filters} onPeriodChange={(days) => changeFilters({ days })} />
    {overviewState.status === "success" && <section className="operation-orders" aria-labelledby="operation-orders-title"><div className="section-heading"><div><h2 id="operation-orders-title">Pedidos da operação</h2><p className="section-description">Uma lista paginada para abrir o número por trás dos indicadores.</p></div></div><OrderFilters filters={filters} branches={overviewState.data.branches} onChange={changeFilters} /><OrderTable state={ordersState} page={filters.page} onPageChange={(page) => changeFilters({ page })} /></section>}
  </div>;
}
