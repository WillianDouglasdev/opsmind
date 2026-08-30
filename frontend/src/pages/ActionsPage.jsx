import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Clock3,
  ListChecks,
  LoaderCircle,
} from "lucide-react";
import { Link } from "react-router-dom";
import { getActions, updateActionStatus } from "../services/api.js";
import { severityLabels } from "../utils/alerts.js";
import { formatDateTime, formatNumber } from "../utils/formatters.js";

const statusLabels = {
  pending: "Pendente",
  in_progress: "Em andamento",
  completed: "Concluída",
};

const statusFilters = [
  { value: "all", label: "Todas" },
  { value: "pending", label: "Pendentes" },
  { value: "in_progress", label: "Em andamento" },
  { value: "completed", label: "Concluídas" },
];

const statusOrder = { pending: 0, in_progress: 1, completed: 2 };
const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };

function sortActions(actions) {
  // Reaplicamos no cliente a mesma ordem da API depois de uma mudança de status.
  return [...actions].sort((left, right) => (
    statusOrder[left.status] - statusOrder[right.status]
    || priorityOrder[left.priority] - priorityOrder[right.priority]
    || new Date(right.created_at) - new Date(left.created_at)
  ));
}

function ActionsPage() {
  const [actions, setActions] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    getActions({ signal: controller.signal })
      .then((data) => {
        setActions(data);
        setLoadError(false);
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setLoadError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, []);

  // KPIs e filtros são locais porque o plano da demo possui poucos itens.
  const summary = useMemo(() => ({
    open: actions.filter((action) => action.status !== "completed").length,
    inProgress: actions.filter((action) => action.status === "in_progress").length,
    completed: actions.filter((action) => action.status === "completed").length,
    priority: actions.filter(
      (action) => action.status !== "completed"
        && ["high", "critical"].includes(action.priority),
    ).length,
  }), [actions]);

  const filteredActions = filter === "all"
    ? actions
    : actions.filter((action) => action.status === filter);

  async function changeStatus(actionId, status) {
    setUpdatingId(actionId);
    setFeedback("");
    try {
      const updated = await updateActionStatus(actionId, status);
      setActions((current) => sortActions(current.map(
        (action) => action.id === actionId ? updated : action,
      )));
      setFeedback(`Status atualizado para ${statusLabels[status].toLowerCase()}.`);
    } catch (requestError) {
      setFeedback(requestError.message || "Não foi possível atualizar a ação.");
    } finally {
      setUpdatingId(null);
    }
  }

  if (loading) {
    return (
      <div className="panel page-state actions-state">
        <LoaderCircle className="spin" size={26} />
        <h2>Carregando plano de ação</h2>
        <p>Reunindo as ações geradas a partir dos sinais operacionais.</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="panel page-state actions-state" role="alert">
        <AlertTriangle size={26} />
        <h2>Plano de ação indisponível</h2>
        <p>Não foi possível consultar as ações agora.</p>
      </div>
    );
  }

  return (
    <div className="actions-page">
      <section className="action-kpi-grid" aria-label="Resumo do plano de ação">
        <article className="panel action-kpi">
          <span><ListChecks size={17} /></span>
          <div><strong>{formatNumber(summary.open)}</strong><small>Ações abertas</small></div>
        </article>
        <article className="panel action-kpi">
          <span><Clock3 size={17} /></span>
          <div><strong>{formatNumber(summary.inProgress)}</strong><small>Em andamento</small></div>
        </article>
        <article className="panel action-kpi">
          <span><CheckCircle2 size={17} /></span>
          <div><strong>{formatNumber(summary.completed)}</strong><small>Concluídas</small></div>
        </article>
        <article className="panel action-kpi warning">
          <span><AlertTriangle size={17} /></span>
          <div><strong>{formatNumber(summary.priority)}</strong><small>Prioridade alta/crítica</small></div>
        </article>
      </section>

      <section className="actions-toolbar">
        <div>
          <span>Itens do plano</span>
          <small>Atualize o status conforme o trabalho avança</small>
        </div>
        <div className="action-filters" aria-label="Filtrar ações por status">
          {statusFilters.map((item) => (
            <button
              type="button"
              key={item.value}
              className={filter === item.value ? "active" : ""}
              aria-pressed={filter === item.value}
              onClick={() => setFilter(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </section>

      {feedback && <p className="action-feedback" role="status">{feedback}</p>}

      {filteredActions.length === 0 ? (
        <section className="panel actions-empty">
          <CircleDot size={24} />
          <h2>{actions.length === 0 ? "Nenhuma ação adicionada" : "Nenhuma ação neste status"}</h2>
          <p>
            {actions.length === 0
              ? "Abra uma investigação e adicione uma das ações sugeridas ao plano."
              : "Selecione outro filtro para consultar os demais itens do plano."}
          </p>
          {actions.length === 0 && <Link to="/alerts">Ver alertas operacionais</Link>}
        </section>
      ) : (
        <div className="action-list">
          {filteredActions.map((action) => (
            <article className={`panel action-card ${action.priority}`} key={action.id}>
              <div className="action-card-main">
                <div className="action-card-badges">
                  <span className={`priority-badge ${action.priority}`}>
                    {severityLabels[action.priority]}
                  </span>
                  <span className={`action-status ${action.status}`}>
                    {statusLabels[action.status]}
                  </span>
                </div>
                <h2>{action.title}</h2>
                <p>{action.description}</p>
                <div className="action-meta">
                  <span>Origem: <Link to={`/alerts/${action.source_alert_key}`}>{action.source_alert_title}</Link></span>
                  <span>Criada em {formatDateTime(action.created_at)}</span>
                  {action.completed_at && <span>Concluída em {formatDateTime(action.completed_at)}</span>}
                </div>
              </div>
              <label className="action-status-control">
                <span>Status</span>
                <select
                  value={action.status}
                  disabled={updatingId === action.id}
                  onChange={(event) => changeStatus(action.id, event.target.value)}
                >
                  <option value="pending">Pendente</option>
                  <option value="in_progress">Em andamento</option>
                  <option value="completed">Concluída</option>
                </select>
              </label>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

export default ActionsPage;
