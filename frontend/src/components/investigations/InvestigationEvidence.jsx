import { ArrowRight, Boxes, PackageCheck, TicketCheck, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";
import { formatAlertMetric } from "../../utils/alerts.js";

const evidenceMeta = {
  delivery: { label: "Entregas", Icon: PackageCheck },
  tickets: { label: "Chamados", Icon: TicketCheck },
  inventory: { label: "Estoque", Icon: Boxes },
  customers: { label: "Clientes", Icon: UsersRound },
};

function EvidenceValue({ value }) {
  if (!value) return null;
  return <div><dt>{value.label}</dt><dd>{formatAlertMetric(value)}</dd></div>;
}

export default function InvestigationEvidence({ evidence }) {
  const additional = evidence.filter((item) => item.importance !== "primary");
  return (
    <section className="investigation-workspace-section" aria-labelledby="operational-evidence-title">
      <div className="investigation-section-heading">
        <p className="eyebrow">Evidências</p>
        <h2 id="operational-evidence-title">Fatos relacionados ao problema</h2>
        <p>Valores calculados a partir dos dados operacionais, com origem identificada.</p>
      </div>
      <div className="evidence-ledger">
        {evidence.map((item) => {
          const { label, Icon } = evidenceMeta[item.type];
          return <article className={`evidence-ledger-row ${item.importance}`} key={item.key}>
            <div className="evidence-ledger-type"><Icon size={17} aria-hidden="true" /><span>{label}</span></div>
            <div className="evidence-ledger-copy"><h3>{item.title}</h3><p>{item.description}</p><small>Fonte: {item.source}</small></div>
            <dl className="evidence-ledger-values"><EvidenceValue value={item.current} /><EvidenceValue value={item.comparison} /><EvidenceValue value={item.difference} /><EvidenceValue value={item.change} /></dl>
            {item.detail_url && <Link to={item.detail_url}>Ver dados relacionados <ArrowRight size={14} aria-hidden="true" /></Link>}
          </article>;
        })}
      </div>
      {additional.length === 0 && <p className="investigation-empty-note">Não encontramos sinais adicionais relacionados a esse atraso.</p>}
    </section>
  );
}
