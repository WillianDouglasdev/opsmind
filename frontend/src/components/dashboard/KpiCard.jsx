import { ArrowRight, Search } from "lucide-react";
import { Link } from "react-router-dom";

// Mantemos o componente de indicador, agora sem repetir caixas e ícones.
// O contexto acompanha cada número para distinguir período, taxa e estado da base.
export default function KpiCard({ metric }) {
  return (
    <article className={"indicator " + metric.id}>
      <h2>{metric.label}</h2>
      <p className="indicator-value">{metric.value}</p>
      <p className="indicator-context">
        <span>{metric.context}</span>
        <small className={`indicator-trend ${metric.trend.tone}`}><i aria-hidden="true" />{metric.trend.label}</small>
      </p>
      {(metric.path || metric.investigationPath) && <nav className="indicator-links" aria-label={`Ações para ${metric.label}`}>
        {metric.path && <Link className="indicator-link" to={metric.path}>Ver detalhes <ArrowRight size={13} aria-hidden="true" /></Link>}
        {metric.investigationPath && <Link className="indicator-link" to={metric.investigationPath}>Investigar <Search size={13} aria-hidden="true" /></Link>}
      </nav>}
    </article>
  );
}
