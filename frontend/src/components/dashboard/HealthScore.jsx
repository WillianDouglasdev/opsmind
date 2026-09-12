import { formatNumber } from "../../utils/formatters.js";

export default function HealthScore({ health }) {
  // A API já classifica a saúde. A interface usa o status para cor e exibe os
  // impactos calculados, sem inventar evolução histórica ou variação do score.
  const tone = {
    "Saudável": "healthy", "Atenção": "attention",
    "Risco moderado": "attention", "Risco alto": "critical",
  }[health.status] ?? "neutral";
  return (
    <section className={"health-overview " + tone} aria-labelledby="health-title">
      <div className="section-heading"><h2 id="health-title">Saúde operacional</h2><span className="health-status"><i aria-hidden="true" />{health.status}</span></div>
      <div className="health-score-line">
        <span className="health-value">{formatNumber(health.score)}</span>
        <div className="health-context"><span>de 100 pontos</span><p>{health.description}</p></div>
      </div>
      <div className="health-track" role="meter" aria-label="Saúde operacional" aria-valuemin={0} aria-valuemax={100} aria-valuenow={health.score} aria-valuetext={health.score + " de 100 — " + health.status}>
        <span style={{ width: Math.max(0, Math.min(100, health.score)) + "%" }} />
      </div>
      <div className="health-track-labels"><span>Mais risco</span><span>Mais saudável</span></div>
      <details className="health-details">
        <summary>Como este resultado é formado <span>{health.components.length} componentes</span></summary>
        <dl>{health.components.map((component) => <div key={component.name}><dt>{component.name}</dt><dd>{component.impact} pontos</dd></div>)}</dl>
        <p>Penalidades calculadas pelo backend sobre a base disponível. Sem histórico de variação do score.</p>
      </details>
    </section>
  );
}
