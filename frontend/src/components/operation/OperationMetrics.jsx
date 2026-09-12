import { formatCurrency, formatNumber, formatPercentage } from "../../utils/formatters.js";

export default function OperationMetrics({ metrics }) {
  const items = [
    ["Pedidos", formatNumber(metrics.orders)],
    ["Atrasos", formatPercentage(metrics.delay_rate, false), `${formatNumber(metrics.delayed_orders)} pedidos`],
    ["Faturamento", formatCurrency(metrics.revenue)],
    ["Clientes", formatNumber(metrics.customers)],
    ["Chamados ativos", formatNumber(metrics.active_tickets), "snapshot da base"],
    ["Estoque crítico", formatNumber(metrics.critical_inventory), "filial × produto"],
  ];
  return <dl className="operation-metrics">{items.map(([label, value, detail]) => <div key={label}><dt>{label}</dt><dd>{value}</dd>{detail && <small>{detail}</small>}</div>)}</dl>;
}
