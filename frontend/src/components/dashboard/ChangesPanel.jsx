import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import SectionState from "../common/SectionState.jsx";

export default function ChangesPanel({ changes, status, onRetry }) {
  // Feed de comparativos, não uma linha do tempo de eventos. Os textos e as
  // direções permanecem os da API; cada item explicita a natureza da comparação.
  return (
    <section className="changes-feed" aria-labelledby="changes-title">
      <div className="section-heading"><h2 id="changes-title">O que mudou</h2><span className="section-kicker">Leitura do período</span></div>
      <p className="section-description">Últimos 30 dias em relação aos 30 dias anteriores.</p>
      {status !== "success" ? <SectionState status={status} onRetry={onRetry} />
        : changes.length === 0 ? <SectionState status="empty" title="Sem comparativos disponíveis" />
          : <ol className="change-feed-list">{changes.map((change) => {
            const Icon = change.direction === "up" ? ArrowUp : change.direction === "down" ? ArrowDown : Minus;
            return <li key={change.id} className={"change-feed-item " + change.tone}>
              <span className="change-feed-mark" aria-hidden="true"><Icon size={16} /></span>
              <div className="change-feed-copy"><span className="change-period">{change.periodLabel}</span><h3>{change.label}</h3><p>{change.description}</p></div>
              <strong className="change-feed-value">{change.displayValue}</strong>
            </li>;
          })}</ol>}
    </section>
  );
}
