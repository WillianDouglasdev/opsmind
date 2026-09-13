import { formatNumber } from "../../utils/formatters.js";

export default function HealthScore({ health }) {
  // A API já classifica a saúde. A interface usa o status para cor e exibe os
  // impactos calculados, sem inventar evolução histórica ou variação do score.
  const tone = {
    "Saudável": "healthy", "Atenção": "attention",
    "Risco moderado": "attention", "Risco alto": "critical",
  }[health.status] ?? "neutral";
  const score = Math.max(0, Math.min(100, Number(health.score) || 0));
  return (
    <section className={"health-overview " + tone} aria-labelledby="health-title">
      <div className="section-heading"><h2 id="health-title">Saúde operacional</h2><span className="health-status"><i aria-hidden="true" />{health.status}</span></div>
      <div className="health-score-layout">
        <div className="health-gauge" role="meter" aria-label="Saúde operacional" aria-valuemin={0} aria-valuemax={100} aria-valuenow={score} aria-valuetext={score + "% — " + health.status} style={{ "--health-score": score + "%" }}>
          <div className="health-gauge-center"><strong>{formatNumber(score)}<span>%</span></strong><small>índice de saúde</small></div>
        </div>
        <div className="health-context"><span>Leitura geral da operação</span><p>{health.description}</p></div>
      </div>
      <details className="health-details">
        <summary>Como este resultado é formado <span>{health.components.length} componentes</span></summary>
        <dl>{health.components.map((component) => <div key={component.name}><dt>{component.name}</dt><dd>{component.impact} pontos</dd></div>)}</dl>
        <p>Penalidades calculadas pelo backend sobre a base disponível. Sem histórico de variação do score.</p>
      </details>
    </section>
  );
}
