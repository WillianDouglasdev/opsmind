import { useEffect, useMemo, useState } from "react";
import { DatabaseZap } from "lucide-react";
import AlertPreview from "../components/dashboard/AlertPreview.jsx";
import ChangesPanel from "../components/dashboard/ChangesPanel.jsx";
import HealthScore from "../components/dashboard/HealthScore.jsx";
import KpiCard from "../components/dashboard/KpiCard.jsx";
import TrendChart from "../components/dashboard/TrendChart.jsx";
import {
  getDashboardChanges,
  getDashboardSummary,
  getDashboardTrends,
} from "../services/api.js";
import {
  formatCurrency,
  formatDate,
  formatNumber,
  formatPercentage,
} from "../utils/formatters.js";

const loadingMetrics = [
  { id: "revenue", label: "Faturamento" },
  { id: "orders", label: "Pedidos" },
  { id: "delays", label: "Pedidos Atrasados" },
  { id: "tickets", label: "Chamados Abertos" },
].map((metric) => ({
  ...metric,
  value: "—",
  change: null,
  direction: "neutral",
  context: "Carregando dados...",
}));

function directionFromChange(value) {
  if (value === null || value === undefined || Number(value) === 0) return "neutral";
  return Number(value) > 0 ? "up" : "down";
}

function toneFromChange(value, positiveIsGood = true) {
  if (value === null || value === undefined || Number(value) === 0) return "neutral";
  return (Number(value) > 0) === positiveIsGood ? "positive" : "risk";
}

function DashboardPage() {
  const [dashboard, setDashboard] = useState({
    summary: null,
    trends: null,
    changes: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function loadDashboard() {
      try {
        const options = { signal: controller.signal };
        // Os três painéis pertencem ao mesmo retrato e podem ser carregados em paralelo.
        const [summary, trends, changes] = await Promise.all([
          getDashboardSummary(options),
          getDashboardTrends(options),
          getDashboardChanges(options),
        ]);
        setDashboard({ summary, trends, changes });
        setError(false);
      } catch (requestError) {
        if (requestError.name !== "AbortError") setError(true);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadDashboard();
    return () => controller.abort();
  }, []);

  const metrics = useMemo(() => {
    const { summary } = dashboard;
    if (!summary) return loadingMetrics;

    return [
      {
        id: "revenue",
        label: "Faturamento",
        value: formatCurrency(summary.revenue.value),
        change: formatPercentage(summary.revenue.change_percentage),
        direction: directionFromChange(summary.revenue.change_percentage),
        tone: toneFromChange(summary.revenue.change_percentage),
        context: "vs. período anterior",
      },
      {
        id: "orders",
        label: "Pedidos",
        value: formatNumber(summary.orders.value),
        change: formatPercentage(summary.orders.change_percentage),
        direction: directionFromChange(summary.orders.change_percentage),
        tone: toneFromChange(summary.orders.change_percentage),
        context: "vs. período anterior",
      },
      {
        id: "delays",
        label: "Pedidos Atrasados",
        value: formatNumber(summary.delayed_orders.value),
        change: formatPercentage(summary.delayed_orders.change_percentage),
        direction: directionFromChange(summary.delayed_orders.change_percentage),
        tone: toneFromChange(summary.delayed_orders.change_percentage, false),
        context: `taxa de ${formatPercentage(summary.delayed_orders.rate, false)}`,
      },
      {
        id: "tickets",
        label: "Chamados Abertos",
        value: formatNumber(summary.open_tickets.value),
        change: null,
        direction: "neutral",
        tone: "neutral",
        context: "abertos ou em andamento",
      },
    ];
  }, [dashboard]);

  const changes = useMemo(
    () => dashboard.changes?.items.map((change, index) => ({
      ...change,
      id: `${change.type}-${index}`,
      displayValue: change.type === "inventory"
        ? `${formatNumber(change.value)} itens`
        : formatPercentage(change.value),
    })) ?? [],
    [dashboard.changes],
  );

  return (
    <div className="container-fluid p-0 dashboard-page">
      <div className="demo-data-note">
        <DatabaseZap size={15} />
        <span>
          <strong>Dados operacionais:</strong>{" "}
          {dashboard.summary
            ? `indicadores calculados até ${formatDate(dashboard.summary.reference_date)}.`
            : error
              ? "indicadores indisponíveis no momento."
              : "carregando indicadores consolidados."}
        </span>
      </div>

      {error && (
        <div className="dashboard-message" role="alert">
          Não foi possível carregar os indicadores agora. Verifique a conexão com a API
          e tente novamente.
        </div>
      )}

      <section className="row g-3 dashboard-top-row" aria-label="Indicadores principais">
        <div className="col-12 col-xxl-5">
          <HealthScore health={dashboard.summary?.operational_health} loading={loading} />
        </div>
        <div className="col-12 col-xxl-7">
          <div className="row g-3 h-100">
            {metrics.map((metric) => (
              <div className="col-12 col-sm-6" key={metric.id}>
                <KpiCard metric={metric} />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="row g-3 mt-0" aria-label="Desempenho e mudanças">
        <div className="col-12 col-xl-8">
          <TrendChart trend={dashboard.trends} loading={loading} />
        </div>
        <div className="col-12 col-xl-4">
          <ChangesPanel changes={changes} loading={loading} />
        </div>
      </section>

      <section className="mt-3" aria-label="Alertas operacionais">
        <AlertPreview />
      </section>
    </div>
  );
}

export default DashboardPage;
