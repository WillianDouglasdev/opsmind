import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BellRing, Filter, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { getAlerts } from "../services/api.js";
import { formatAlertMetric, severityLabels } from "../utils/alerts.js";

const severityFilters = [
  { value: "all", label: "Todos" },
  { value: "critical", label: "Críticos" },
  { value: "high", label: "Altos" },
  { value: "medium", label: "Médios" },
  { value: "low", label: "Baixos" },
];

function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [selectedSeverity, setSelectedSeverity] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    getAlerts({ signal: controller.signal })
      .then((data) => {
        setAlerts(data);
        setError(false);
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, []);

  // A lista é pequena e já está em memória, então outro filtro no backend não traria ganho.
  const filteredAlerts = useMemo(
    () => selectedSeverity === "all"
      ? alerts
      : alerts.filter((alert) => alert.severity === selectedSeverity),
    [alerts, selectedSeverity],
  );

  return (
    <div className="alerts-page">
      <section className="panel alerts-page-intro">
        <div className="alerts-intro-copy">
          <span className="feature-icon alerts">
            <BellRing size={24} />
          </span>
          <div>
            <h2>Alertas Operacionais</h2>
            <p>Sinais detectados automaticamente a partir dos dados da operação.</p>
          </div>
        </div>
        <span className="alerts-count">
          <strong>{alerts.length}</strong> alertas ativos
        </span>
      </section>

      <div className="severity-filter" aria-label="Filtrar alertas por severidade">
        <span><Filter size={14} /> Severidade</span>
        {severityFilters.map((filter) => (
          <button
            className={selectedSeverity === filter.value ? "active" : ""}
            type="button"
            key={filter.value}
            aria-pressed={selectedSeverity === filter.value}
            onClick={() => setSelectedSeverity(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {error ? (
        <div className="panel page-state" role="alert">
          <BellRing size={24} />
          <h2>Não foi possível carregar os alertas</h2>
          <p>Verifique a conexão com a API e tente novamente.</p>
        </div>
      ) : loading ? (
        <div className="panel page-state">
          <BellRing size={24} />
          <h2>Analisando sinais operacionais</h2>
          <p>As regras determinísticas estão sendo aplicadas aos dados.</p>
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="panel page-state">
          <BellRing size={24} />
          <h2>Nenhum alerta nesta severidade</h2>
          <p>Selecione outro filtro para revisar os sinais ativos.</p>
        </div>
      ) : (
        <section className="alert-catalog" aria-label="Alertas ativos">
          {filteredAlerts.map((alert) => (
            <article className={`panel alert-overview-card ${alert.severity}`} key={alert.key}>
              <div className="alert-overview-main">
                <span className={`severity-badge ${alert.severity}`}>
                  {severityLabels[alert.severity]}
                </span>
                <h2>{alert.title}</h2>
                <p>{alert.summary}</p>
                <div className="alert-metric-list">
                  {alert.metrics.slice(0, 3).map((metric) => (
                    <span key={metric.label}>
                      <strong>{formatAlertMetric(metric)}</strong>
                      {metric.label}
                    </span>
                  ))}
                </div>
              </div>
              <nav className="alert-card-links" aria-label={`Ações para ${alert.title}`}>
                <Link className="investigate-link" to={`/alerts/${alert.key}`}>Ver alerta <ArrowRight size={15} /></Link>
                {["DELIVERY_DELAY_INCREASE", "BRANCH_PERFORMANCE"].includes(alert.type) && <Link className="investigate-link" to="/investigations/delivery-delays?days=30">Investigar evidências <Search size={15} /></Link>}
              </nav>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}

export default AlertsPage;
