import { useCallback } from "react";
import { ArrowRight, SearchCheck } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import SectionState from "../components/common/SectionState.jsx";
import PeriodSelector from "../components/operation/PeriodSelector.jsx";
import useApiResource from "../hooks/useApiResource.js";
import { getInvestigations } from "../services/api.js";
import { severityLabels } from "../utils/alerts.js";
import { formatNumber, formatPercentage } from "../utils/formatters.js";
import {
  investigationPath,
  investigationSearchParams,
  readInvestigationFilters,
} from "../utils/investigations.js";

export function InvestigationsList({ state, filters, onPeriodChange }) {
  if (state.status !== "success") {
    return <SectionState status={state.status} title={state.status === "loading" ? "Reunindo investigações…" : undefined} onRetry={state.retry} />;
  }
  return (
    <div className="investigations-index">
      <div className="investigations-toolbar"><p>Investigações derivadas dos dados atuais.</p><PeriodSelector value={filters.days} onChange={onPeriodChange} /></div>
      {state.data.items.length === 0 ? (
        <SectionState status="empty" title="Nenhuma investigação disponível" description="Não há pedidos atrasados no período selecionado. Isso é um resultado válido." />
      ) : (
        <section className="investigation-catalog" aria-labelledby="investigation-catalog-title">
          <div className="investigation-section-heading"><p className="eyebrow">Disponível agora</p><h2 id="investigation-catalog-title">Atrasos de entrega</h2><p>Esta primeira versão investiga um tipo de situação com profundidade e transparência.</p></div>
          {state.data.items.map((item) => <article className="investigation-catalog-row" key={item.key}>
            <div className="investigation-catalog-icon"><SearchCheck size={22} aria-hidden="true" /></div>
            <div><span className={`severity-badge ${item.severity}`}>{severityLabels[item.severity]}</span><h3>{item.title}</h3><p>{item.description}</p></div>
            <dl><div><dt>Filial mais afetada</dt><dd>{item.branch.name}</dd></div><div><dt>Taxa</dt><dd>{formatPercentage(item.delay_rate, false)}</dd></div><div><dt>Pedidos envolvidos</dt><dd>{formatNumber(item.delayed_orders)}</dd></div></dl>
            <Link className="primary-link" to={item.detail_url || investigationPath(filters, { branch: item.branch.id })}>Investigar <ArrowRight size={15} aria-hidden="true" /></Link>
          </article>)}
        </section>
      )}
    </div>
  );
}

export default function InvestigationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = readInvestigationFilters(searchParams);
  const loader = useCallback((options) => getInvestigations(filters.days, options), [filters.days]);
  const state = useApiResource(loader);
  return <InvestigationsList state={state} filters={filters} onPeriodChange={(days) => setSearchParams(investigationSearchParams(filters, { days }))} />;
}
