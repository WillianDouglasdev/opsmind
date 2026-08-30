import { useEffect, useState } from "react";
import { ArrowRight, BellRing } from "lucide-react";
import { Link } from "react-router-dom";
import { getAlerts } from "../../services/api.js";
import { severityLabels } from "../../utils/alerts.js";

function AlertPreview() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    getAlerts({ signal: controller.signal })
      .then((data) => {
        // A API já ordena por severidade; o dashboard mostra apenas os três primeiros.
        setAlerts(data.slice(0, 3));
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

  return (
    <article className="panel alerts-card">
      <div className="panel-heading alerts-heading">
        <div>
          <h2>Alertas Operacionais</h2>
          <p>Sinais que exigem atenção</p>
        </div>
        <Link to="/alerts" className="text-link">
          Ver todos <ArrowRight size={14} />
        </Link>
      </div>

      <div className="alert-list">
        {alerts.map((alert) => (
          <Link className="alert-item" to={`/alerts/${alert.key}`} key={alert.key}>
            <span className={`severity-marker ${alert.severity}`} />
            <div className="alert-copy">
              <span className={`severity-badge ${alert.severity}`}>
                {severityLabels[alert.severity]}
              </span>
              <h3>{alert.title}</h3>
              <p>{alert.summary}</p>
            </div>
            <ArrowRight className="alert-arrow" size={17} aria-hidden="true" />
          </Link>
        ))}

        {(loading || error || (!loading && alerts.length === 0)) && (
          <div className="alert-empty-state">
            <BellRing size={20} />
            <div>
              <h3>
                {loading
                  ? "Analisando sinais operacionais"
                  : error
                    ? "Alertas indisponíveis"
                    : "Nenhum alerta ativo"}
              </h3>
              <p>
                {error
                  ? "Não foi possível consultar os alertas agora."
                  : loading
                    ? "Aplicando regras determinísticas aos dados da operação."
                    : "As regras atuais não identificaram sinais que exijam investigação."}
              </p>
            </div>
          </div>
        )}
      </div>
    </article>
  );
}

export default AlertPreview;
