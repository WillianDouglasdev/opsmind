import { Info, ListChecks } from "lucide-react";

function HealthScore({ health, loading }) {
  const score = health?.score ?? 0;
  // O anel usa graus no gradiente, por isso cada ponto do score representa 3,6 graus.
  const scoreAngle = `${score * 3.6}deg`;
  const status = loading ? "Calculando" : health?.status ?? "Indisponível";
  const description = loading
    ? "Consolidando os indicadores operacionais."
    : health?.description ?? "Não foi possível calcular a saúde operacional.";

  return (
    <article className="panel health-card">
      <div className="panel-heading">
        <div>
          <p className="panel-eyebrow">Status Atual</p>
          <h2>Saúde Operacional</h2>
        </div>
        <span className="info-icon" title="Pontuação operacional consolidada">
          <Info size={17} />
        </span>
      </div>

      <div className="health-content">
        <div
          className={`health-ring ${health ? "" : "is-loading"}`}
          style={{ "--score-angle": scoreAngle }}
          role="img"
          aria-label={health ? `Saúde operacional: ${score} de 100` : status}
        >
          <span>
            <strong>{health ? score : "—"}</strong>
            <small>/ 100</small>
          </span>
        </div>

        <div className="health-summary">
          <span className="risk-badge">{status}</span>
          <p>{description}</p>
          {health && (
            <span className="health-trend">
              <ListChecks size={14} />
              {health.components.length} componentes avaliados
            </span>
          )}
        </div>
      </div>
    </article>
  );
}

export default HealthScore;
