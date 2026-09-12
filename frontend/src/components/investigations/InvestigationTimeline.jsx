import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { formatDate, formatNumber } from "../../utils/formatters.js";

export default function InvestigationTimeline({ timeline }) {
  return (
    <section className="investigation-workspace-section timeline-section" aria-labelledby="timeline-title">
      <div className="investigation-section-heading">
        <p className="eyebrow">Linha do tempo</p>
        <h2 id="timeline-title">Dias com pedidos atrasados</h2>
        <p>Cronologia derivada dos registros reais da filial; datas sem atraso não são inventadas.</p>
      </div>
      {timeline.length === 0 ? <p className="investigation-empty-note">Não há eventos suficientes para montar uma cronologia neste recorte.</p> : (
        <ol className="investigation-timeline">
          {timeline.map((event) => <li key={`${event.date}-${event.type}`}>
            <time dateTime={event.date}>{formatDate(event.date)}</time>
            <div><h3>{event.title}</h3><p>{event.description}</p><small>{formatNumber(event.value)} pedidos · {event.source}</small></div>
            {event.detail_url && <Link to={event.detail_url} aria-label={`Ver pedidos relacionados a ${formatDate(event.date)}`}>Ver pedidos <ArrowRight size={13} aria-hidden="true" /></Link>}
          </li>)}
        </ol>
      )}
    </section>
  );
}
