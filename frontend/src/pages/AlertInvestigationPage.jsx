import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ChartNoAxesCombined,
  Check,
  ClipboardPlus,
  Lightbulb,
  Link2,
  LoaderCircle,
  SearchCheck,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
import {
  createAction,
  getAlertInvestigation,
  getAlertRecommendations,
} from "../services/api.js";
import { formatAlertMetric, severityLabels } from "../utils/alerts.js";

function MetricGrid({ metrics }) {
  return (
    <div className="investigation-metric-grid">
      {metrics.map((metric) => (
        <article className="panel investigation-metric" key={metric.label}>
          <strong>{formatAlertMetric(metric)}</strong>
          <span>{metric.label}</span>
        </article>
      ))}
    </div>
  );
}

function EvidenceSection({ item }) {
  return (
    <article className="panel evidence-card">
      <h3>{item.title}</h3>
      <p>{item.description}</p>
      <div className="evidence-metrics">
        {item.metrics.map((metric) => (
          <span key={metric.label}>
            <small>{metric.label}</small>
            <strong>{formatAlertMetric(metric)}</strong>
          </span>
        ))}
      </div>
    </article>
  );
}

function AlertInvestigationPage() {
  const { alertKey } = useParams();
  const [investigation, setInvestigation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorStatus, setErrorStatus] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(true);
  const [recommendationsError, setRecommendationsError] = useState(false);
  const [creatingKey, setCreatingKey] = useState(null);
  const [recommendationFeedback, setRecommendationFeedback] = useState({});

  useEffect(() => {
    const controller = new AbortController();

    getAlertInvestigation(alertKey, { signal: controller.signal })
      .then((data) => {
        setInvestigation(data);
        setErrorStatus(null);
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setErrorStatus(requestError.status ?? 500);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [alertKey]);

  useEffect(() => {
    const controller = new AbortController();

    // Recomendações carregam separadamente para não bloquear a leitura da investigação.
    getAlertRecommendations(alertKey, { signal: controller.signal })
      .then((data) => {
        setRecommendations(data);
        setRecommendationsError(false);
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setRecommendationsError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setRecommendationsLoading(false);
      });

    return () => controller.abort();
  }, [alertKey]);

  async function addRecommendation(recommendationKey) {
    setCreatingKey(recommendationKey);
    setRecommendationFeedback((current) => ({ ...current, [recommendationKey]: "" }));
    try {
      await createAction(alertKey, recommendationKey);
      setRecommendations((current) => current.map((item) => (
        item.recommendation_key === recommendationKey
          ? { ...item, is_added: true }
          : item
      )));
      setRecommendationFeedback((current) => ({
        ...current,
        [recommendationKey]: "Adicionada ao plano.",
      }));
    } catch (requestError) {
      const isDuplicate = requestError.status === 409;
      // O 409 também confirma que a recomendação já está representada no plano.
      if (isDuplicate) {
        setRecommendations((current) => current.map((item) => (
          item.recommendation_key === recommendationKey
            ? { ...item, is_added: true }
            : item
        )));
      }
      setRecommendationFeedback((current) => ({
        ...current,
        [recommendationKey]: isDuplicate
          ? "A ação já está no plano."
          : "Não foi possível adicionar a ação.",
      }));
    } finally {
      setCreatingKey(null);
    }
  }

  if (loading) {
    return (
      <div className="panel page-state investigation-state">
        <SearchCheck size={26} />
        <h2>Preparando investigação</h2>
        <p>Reunindo impacto, evidências e sinais relacionados.</p>
      </div>
    );
  }

  if (errorStatus) {
    return (
      <div className="panel page-state investigation-state" role="alert">
        <AlertTriangle size={26} />
        <h2>{errorStatus === 404 ? "Alerta não encontrado" : "Investigação indisponível"}</h2>
        <p>
          {errorStatus === 404
            ? "O alerta informado não existe ou não está mais ativo."
            : "Não foi possível consultar as evidências agora."}
        </p>
        <Link className="back-link" to="/alerts"><ArrowLeft size={14} /> Voltar aos alertas</Link>
      </div>
    );
  }

  const { alert } = investigation;

  return (
    <div className="investigation-page">
      <nav className="investigation-breadcrumb" aria-label="Navegação estrutural">
        <Link to="/alerts">Alertas</Link><span>/</span><span>Investigação</span>
      </nav>

      <header className={`panel investigation-header ${alert.severity}`}>
        <span className={`severity-badge ${alert.severity}`}>
          {severityLabels[alert.severity]}
        </span>
        <h2>{alert.title}</h2>
        <p className="investigation-summary">{alert.summary}</p>
        <p className="investigation-context">{investigation.context}</p>
      </header>

      <section className="investigation-section" aria-labelledby="impact-title">
        <div className="section-title">
          <ChartNoAxesCombined size={18} />
          <div><span>Impacto</span><h2 id="impact-title">Dimensão do sinal operacional</h2></div>
        </div>
        <MetricGrid metrics={investigation.impact} />
      </section>

      {investigation.related_signals.length > 0 && (
        <section className="investigation-section" aria-labelledby="signals-title">
          <div className="section-title">
            <Link2 size={18} />
            <div><span>Fatores associados</span><h2 id="signals-title">Sinais relacionados</h2></div>
          </div>
          <div className="evidence-grid related-grid">
            {investigation.related_signals.map((item) => (
              <EvidenceSection item={item} key={item.title} />
            ))}
          </div>
        </section>
      )}

      <section className="investigation-section" aria-labelledby="evidence-title">
        <div className="section-title">
          <SearchCheck size={18} />
          <div><span>Evidências</span><h2 id="evidence-title">Dados que sustentam o alerta</h2></div>
        </div>
        <div className="evidence-grid">
          {investigation.evidence.map((item) => (
            <EvidenceSection item={item} key={`${item.title}-${item.description}`} />
          ))}
        </div>
      </section>

      <section className="investigation-section" aria-labelledby="recommendations-title">
        <div className="section-title">
          <Lightbulb size={18} />
          <div><span>Próximos passos</span><h2 id="recommendations-title">Ações sugeridas</h2></div>
        </div>

        {recommendationsLoading && (
          <div className="panel recommendations-state">
            <LoaderCircle className="spin" size={18} /> Calculando ações a partir das evidências...
          </div>
        )}

        {recommendationsError && (
          <div className="panel recommendations-state error" role="alert">
            <AlertTriangle size={18} /> Não foi possível consultar as ações sugeridas.
          </div>
        )}

        {!recommendationsLoading && !recommendationsError && (
          <div className="recommendation-grid">
            {recommendations.map((recommendation) => (
              <article
                className={`panel recommendation-card ${recommendation.priority}`}
                key={recommendation.recommendation_key}
              >
                <div className="recommendation-heading">
                  <span className={`priority-badge ${recommendation.priority}`}>
                    {severityLabels[recommendation.priority]}
                  </span>
                  <ClipboardPlus size={18} />
                </div>
                <h3>{recommendation.title}</h3>
                <p>{recommendation.description}</p>
                <div className="recommendation-reason">
                  <strong>Por que esta ação?</strong>
                  <span>{recommendation.reason}</span>
                </div>
                <button
                  type="button"
                  disabled={recommendation.is_added || creatingKey === recommendation.recommendation_key}
                  onClick={() => addRecommendation(recommendation.recommendation_key)}
                >
                  {recommendation.is_added
                    ? <><Check size={15} /> Adicionada</>
                    : creatingKey === recommendation.recommendation_key
                      ? <><LoaderCircle className="spin" size={15} /> Adicionando...</>
                      : <><ClipboardPlus size={15} /> Adicionar às ações</>}
                </button>
                {recommendationFeedback[recommendation.recommendation_key] && (
                  <small className="recommendation-feedback" role="status">
                    {recommendationFeedback[recommendation.recommendation_key]}
                  </small>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default AlertInvestigationPage;
