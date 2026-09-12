import { ArrowRight, CheckCircle2 } from "lucide-react";
import { Link } from "react-router-dom";

export default function InvestigationNextSteps({ steps }) {
  return (
    <section className="investigation-workspace-section next-steps-section" aria-labelledby="next-steps-title">
      <div className="investigation-section-heading">
        <p className="eyebrow">Próximos passos</p>
        <h2 id="next-steps-title">Sugestões baseadas em regras</h2>
        <p>Orientações para continuar a análise; ainda não são itens do Plano de ação.</p>
      </div>
      <ol className="investigation-next-steps">
        {steps.map((step, index) => <li key={step.key}>
          <span>{String(index + 1).padStart(2, "0")}</span>
          <CheckCircle2 size={18} aria-hidden="true" />
          <div><h3>{step.title}</h3><p>{step.description}</p></div>
          {step.detail_url && <Link to={step.detail_url}>Abrir contexto <ArrowRight size={13} aria-hidden="true" /></Link>}
        </li>)}
      </ol>
    </section>
  );
}
