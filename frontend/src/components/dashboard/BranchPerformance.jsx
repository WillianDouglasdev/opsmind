import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import { branchRows, operationPath } from "../../utils/operation.js";
import { formatNumber, formatPercentage } from "../../utils/formatters.js";
import SectionState from "../common/SectionState.jsx";

export default function BranchPerformance({ section, onRetry }) {
  const rows = branchRows(section.data).slice(0, 3);
  return (
    <section className="branch-performance" aria-labelledby="branches-title">
      <div className="section-heading"><h2 id="branches-title">Filiais</h2><Link className="text-button" to="/operation?days=30">Ver operação</Link></div>
      <p className="section-description">Unidades com maior taxa de atraso no período.</p>
      {section.status !== "success" ? <SectionState status={section.status} onRetry={onRetry} />
        : rows.length === 0 ? <SectionState status="empty" title="Sem comparação disponível" description="Nenhuma filial com evidências de desempenho disponíveis nos alertas atuais." />
          : <div className="branch-list">{rows.map((row) => (
            <div className="branch-row" key={row.id}>
              <div className="branch-row-heading"><Link to={operationPath(`/operation/branches/${row.id}`, { days: 30, branch: "", status: "", delivery: "all", page: 1 })}>{row.name}<ArrowUpRight size={15} aria-hidden="true" /></Link><strong>{formatPercentage(row.delay_rate, false)}</strong></div>
              <div className="branch-bar" role="img" aria-label={`${row.name}: ${formatPercentage(row.delay_rate, false)} de atrasos. Média das filiais: ${formatPercentage(section.data.branch_average.delay_rate, false)}.`}>
                <span style={{ width: `${Math.max(0, Math.min(100, row.delay_rate))}%` }} />
                <i style={{ left: `${Math.max(0, Math.min(100, section.data.branch_average.delay_rate ?? 0))}%` }} />
              </div>
              <p>{formatNumber(row.orders)} pedidos <span>Média das filiais: {formatPercentage(section.data.branch_average.delay_rate, false)}</span></p>
            </div>
          ))}</div>}
      <p className="scope-note">Abra uma filial para comparar sua operação e consultar os pedidos.</p>
    </section>
  );
}
