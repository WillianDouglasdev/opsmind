import { useCallback } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import BranchComparison from "../components/operation/BranchComparison.jsx";
import BranchDelayTrend from "../components/operation/BranchDelayTrend.jsx";
import OrderFilters from "../components/operation/OrderFilters.jsx";
import OrderTable from "../components/operation/OrderTable.jsx";
import PeriodSelector from "../components/operation/PeriodSelector.jsx";
import SectionState from "../components/common/SectionState.jsx";
import useApiResource from "../hooks/useApiResource.js";
import { getOperationBranch, getOperationOrders } from "../services/api.js";
import { formatCurrency, formatNumber, formatPercentage } from "../utils/formatters.js";
import { operationPath, operationSearchParams, readOperationFilters } from "../utils/operation.js";

export default function OperationBranchPage() {
  const { branchId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = readOperationFilters(searchParams);
  const loadBranch = useCallback((options) => getOperationBranch(branchId, filters.days, options), [branchId, filters.days]);
  const loadOrders = useCallback((options) => getOperationOrders({ days: filters.days, branch: branchId, status: filters.status, delivery: filters.delivery, page: filters.page, page_size: 12 }, options), [branchId, filters.days, filters.status, filters.delivery, filters.page]);
  const branchState = useApiResource(loadBranch);
  const ordersState = useApiResource(loadOrders);
  const changeFilters = (changes) => setSearchParams((current) => operationSearchParams({ ...readOperationFilters(current), branch: "" }, changes));
  if (branchState.status !== "success") return <SectionState status={branchState.status} title={branchState.status === "loading" ? "Abrindo a filial…" : branchState.error?.status === 404 ? "Filial não encontrada" : undefined} onRetry={branchState.retry} />;
  const data = branchState.data;
  const metrics = data.metrics;
  return <div className="branch-detail-page">
    <div className="operation-toolbar"><Link className="text-button" to={operationPath("/operation", filters, { branch: "" })}>← Voltar para Operação</Link><PeriodSelector value={filters.days} onChange={(days) => changeFilters({ days })} /></div>
    <section className="branch-opening" aria-labelledby="branch-name"><div><p className="eyebrow">Filial · {data.branch.city}, {data.branch.state}</p><h2 id="branch-name">{data.branch.name}</h2><p>{data.period.days} dias até {data.period.end_date.split("-").reverse().join("/")}</p></div><div className="branch-health"><span>Saúde operacional</span>{metrics.health ? <><strong>{metrics.health.score}<small>/100</small></strong><p>{metrics.health.status}</p></> : <strong className="without-base">Sem base</strong>}</div></section>
    <dl className="branch-metrics"><div><dt>Pedidos</dt><dd>{formatNumber(metrics.orders)}</dd></div><div><dt>Atrasos</dt><dd>{formatPercentage(metrics.delay_rate, false)}</dd><small>{formatNumber(metrics.delayed_orders)} pedidos</small></div><div><dt>Receita</dt><dd>{formatCurrency(metrics.revenue)}</dd></div><div><dt>Clientes afetados</dt><dd>{formatNumber(metrics.impacted_customers)}</dd></div><div><dt>Chamados ativos</dt><dd>{formatNumber(metrics.active_tickets)}</dd></div><div><dt>Estoque crítico</dt><dd>{formatNumber(metrics.critical_inventory)}</dd></div></dl>
    <div className="branch-analysis"><BranchDelayTrend points={data.trend} /><BranchComparison comparisons={data.comparisons} scope={data.comparison_scope} /></div>
    <section className="branch-contributors" aria-labelledby="contributors-title"><div className="section-heading"><h2 id="contributors-title">O que contribui para o resultado</h2></div><dl><div><dt>Pedidos atrasados</dt><dd>{formatNumber(metrics.delayed_orders)}</dd></div><div><dt>Clientes impactados</dt><dd>{formatNumber(metrics.impacted_customers)}</dd></div><div><dt>Chamados ativos vinculados</dt><dd>{formatNumber(metrics.active_tickets)}</dd></div><div><dt>Itens de estoque crítico</dt><dd>{formatNumber(metrics.critical_inventory)}</dd></div></dl><p>São sinais do mesmo recorte operacional; esta tela não atribui causalidade.</p></section>
    <section className="operation-orders branch-orders" aria-labelledby="branch-orders-title"><div className="section-heading"><div><h2 id="branch-orders-title">Pedidos da filial</h2><p className="section-description">Filtre o conjunto que sustenta os números acima.</p></div></div><OrderFilters filters={filters} showBranch={false} onChange={changeFilters} /><OrderTable state={ordersState} page={filters.page} onPageChange={(page) => changeFilters({ page })} /></section>
  </div>;
}
