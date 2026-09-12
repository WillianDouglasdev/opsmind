import { RefreshCw } from "lucide-react";
import HealthScore from "../components/dashboard/HealthScore.jsx";
import AlertPreview from "../components/dashboard/AlertPreview.jsx";
import ChangesPanel from "../components/dashboard/ChangesPanel.jsx";
import TrendChart from "../components/dashboard/TrendChart.jsx";
import KpiCard from "../components/dashboard/KpiCard.jsx";
import DataFlow from "../components/dashboard/DataFlow.jsx";
import BranchPerformance from "../components/dashboard/BranchPerformance.jsx";
import SectionState from "../components/common/SectionState.jsx";
import useDashboardData from "../hooks/useDashboardData.js";
import { buildChangeFeed, buildIndicators } from "../utils/dashboard.js";
import { formatDate, formatDateTime } from "../utils/formatters.js";
import { demoMetadata } from "../data/demoMetadata.js";

export default function DashboardPage() {
  const { sections, consultedAt, refresh, loading } = useDashboardData();
  const summary = sections.summary.data;
  const hasOrders = summary && summary.orders.value > 0;
  const indicators = buildIndicators(summary);

  // A composição começa pelo estado da operação e por prioridades. Indicadores
  // complementam a leitura; comparativos e origem dos dados têm espaços próprios.
  // Data da consulta é do navegador, referência analítica vem da API: não são freshness.
  return (
    <div className="dashboard-page">
      <header className="home-opening">
        <div>
          <p className="eyebrow">{demoMetadata.organization} <span>/</span> Resumo operacional</p>
          <h1>A operação, em perspectiva.</h1>
          <p>O que mudou. O que merece atenção. Por onde começar.</p>
        </div>
        <button className="quiet-button refresh-button" type="button" onClick={refresh} disabled={loading} aria-label="Atualizar dados">
          <RefreshCw size={15} className={loading ? "spin" : ""} aria-hidden="true" />
          {loading ? "Consultando" : "Atualizar"}
        </button>
      </header>

      <div className="home-period">
        <span>{summary ? "Últimos 30 dias até " + formatDate(summary.reference_date) : sections.summary.status === "loading" ? "Consultando referência dos indicadores…" : "Referência dos indicadores indisponível"}</span>
        <span>{consultedAt ? "Consultado em " + formatDateTime(consultedAt) : "Dados da demonstração"}</span>
      </div>

      <div className="home-primary">
        {sections.summary.status !== "success"
          ? <SectionState status={sections.summary.status} title={sections.summary.status === "loading" ? "Reunindo o resumo da operação…" : undefined} onRetry={refresh} />
          : hasOrders
            ? <HealthScore health={summary.operational_health} />
            : <SectionState status="empty" title="Sem pedidos neste período" description="Não há base de pedidos para interpretar a saúde operacional. Consulte os demais sinais disponíveis." />}
        <AlertPreview section={sections.alerts} onRetry={refresh} />
      </div>

      {summary && <section className="indicator-strip" aria-label="Indicadores complementares">
        {indicators.map((metric) => <KpiCard metric={metric} key={metric.id} />)}
      </section>}

      <div className="home-analysis">
        <ChangesPanel changes={buildChangeFeed(sections.changes.data?.items)} status={sections.changes.status} onRetry={refresh} />
        <DataFlow referenceDate={summary?.reference_date} section={sections.pipeline} onRetry={refresh} />
      </div>

      <div className="home-performance">
        <TrendChart trend={sections.trends.data} status={sections.trends.status} onRetry={refresh} />
        <BranchPerformance section={sections.branches} onRetry={refresh} />
      </div>
      <footer className="home-footnote">Cenário de demonstração. Os sinais orientam a investigação; não comprovam uma relação de causa.</footer>
    </div>
  );
}
