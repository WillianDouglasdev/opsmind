import { formatCurrency, formatDateTime } from "../../utils/formatters.js";
import SectionState from "../common/SectionState.jsx";

export default function OrderTable({ state, page, onPageChange }) {
  if (state.status !== "success") return <SectionState status={state.status} onRetry={state.retry} />;
  if (!state.data.results.length) return <SectionState status="empty" title="Nenhum pedido neste recorte" description="A combinação atual de período e filtros não encontrou pedidos." />;
  const data = state.data;
  return <>
    <div className="operation-table-wrap order-table-wrap"><table className="operation-table order-table">
      <caption>Pedidos filtrados da operação</caption>
      <thead><tr><th scope="col">Pedido</th><th scope="col">Cliente</th><th scope="col">Filial</th><th scope="col">Data</th><th scope="col">Valor</th><th scope="col">Status</th><th scope="col">Entrega</th></tr></thead>
      <tbody>{data.results.map((order) => <tr key={order.id}><th scope="row">{order.identifier}</th><td data-label="Cliente">{order.customer.name}</td><td data-label="Filial">{order.branch.name}</td><td data-label="Data"><time dateTime={order.created_at}>{formatDateTime(order.created_at)}</time></td><td data-label="Valor">{formatCurrency(order.total_amount)}</td><td data-label="Status"><span className={`operation-status ${order.status}`}>{order.status_label}</span></td><td data-label="Entrega"><span className={`delivery-state ${order.delivery_state}`}>{order.delivery_state_label}</span></td></tr>)}</tbody>
    </table></div>
    <nav className="operation-pagination" aria-label="Paginação de pedidos"><span>{data.count} pedidos · página {data.page} de {data.total_pages}</span><div><button type="button" className="quiet-button" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>Anterior</button><button type="button" className="quiet-button" disabled={page >= data.total_pages} onClick={() => onPageChange(page + 1)}>Próxima</button></div></nav>
  </>;
}
