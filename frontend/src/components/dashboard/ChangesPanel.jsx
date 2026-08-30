import { ArrowDown, ArrowUp, Minus } from "lucide-react";

function ChangesPanel({ changes, loading }) {
  return (
    <article className="panel changes-card">
      <div className="panel-heading compact-heading">
        <div>
          <h2>O que mudou?</h2>
          <p>Últimos 30 dias vs. período anterior</p>
        </div>
      </div>

      <div className="changes-list">
        {changes.length > 0 ? changes.map((change) => {
          const DirectionIcon = change.direction === "down"
            ? ArrowDown
            : change.direction === "up"
              ? ArrowUp
              : Minus;
          return (
            <div className="change-item" key={change.id} title={change.description}>
              <span className={`change-icon ${change.tone}`}>
                <DirectionIcon size={15} />
              </span>
              <span className="change-label">{change.label}</span>
              <strong className={change.tone}>{change.displayValue}</strong>
            </div>
          );
        }) : (
          <div className="data-placeholder">
            {loading ? "Carregando comparativos..." : "Comparativos indisponíveis."}
          </div>
        )}
      </div>
    </article>
  );
}

export default ChangesPanel;
