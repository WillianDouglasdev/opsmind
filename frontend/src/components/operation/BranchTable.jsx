import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import { formatCurrency, formatNumber, formatPercentage } from "../../utils/formatters.js";
import { branchRows, operationPath } from "../../utils/operation.js";

export default function BranchTable({ overview, filters }) {
  const rows = branchRows(overview);
  return (
    <div className="operation-table-wrap branch-table-wrap">
      <table className="operation-table">
        <caption>Comparação das filiais no período selecionado</caption>
        <thead><tr><th scope="col">Filial</th><th scope="col">Saúde</th><th scope="col">Pedidos</th><th scope="col">Atrasos</th><th scope="col">Receita</th><th scope="col">Chamados</th><th scope="col"><span className="visually-hidden">Abrir</span></th></tr></thead>
        <tbody>{rows.map((branch) => <tr key={branch.id} className="interactive-row">
          <th scope="row"><Link to={operationPath(`/operation/branches/${branch.id}`, filters)}>{branch.name}<small>{branch.city} · {branch.state}</small></Link></th>
          <td data-label="Saúde">{branch.health ? <><strong>{branch.health.score}</strong><small>{branch.health.status}</small></> : "Sem base"}</td>
          <td data-label="Pedidos">{formatNumber(branch.orders)}</td>
          <td data-label="Atrasos"><strong className={branch.delay_rate > overview.metrics.delay_rate ? "metric-worse" : ""}>{formatPercentage(branch.delay_rate, false)}</strong><small>{formatNumber(branch.delayed_orders)} pedidos</small></td>
          <td data-label="Receita">{formatCurrency(branch.revenue)}</td>
          <td data-label="Chamados">{formatNumber(branch.active_tickets)}</td>
          <td><Link className="table-action" aria-label={`Abrir filial ${branch.name}`} to={operationPath(`/operation/branches/${branch.id}`, filters)}><ArrowUpRight size={16} aria-hidden="true" /></Link></td>
        </tr>)}</tbody>
      </table>
    </div>
  );
}
