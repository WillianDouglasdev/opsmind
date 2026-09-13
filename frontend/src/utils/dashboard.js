import { formatCurrency, formatNumber, formatPercentage } from "./formatters.js";

export function buildIndicators(summary) {
  if (!summary) return [];
  const comparison = (value, improvesWhen = "up") => {
    if (value === null) return { context: "Sem base de comparação", trend: { tone: "neutral", label: "Sem comparação" } };
    if (value === 0) return { context: `${formatPercentage(value)} vs. período anterior`, trend: { tone: "neutral", label: "Estável" } };
    const improved = improvesWhen === "up" ? value > 0 : value < 0;
    return {
      context: `${formatPercentage(value)} vs. período anterior`,
      trend: { tone: improved ? "positive" : "negative", label: improved ? "Melhor" : "Pior" },
    };
  };
  const revenue = comparison(summary.revenue.change_percentage);
  const orders = comparison(summary.orders.change_percentage);
  const delays = comparison(summary.delayed_orders.change_percentage, "down");
  // Adaptamos unidades e contexto. Nenhuma soma, taxa ou classificação é recalculada.
  return [
    { id: "revenue", label: "Faturamento", value: formatCurrency(summary.revenue.value), context: revenue.context, trend: revenue.trend },
    { id: "orders", label: "Pedidos", value: formatNumber(summary.orders.value), context: orders.context, trend: orders.trend },
    { id: "delays", label: "Pedidos atrasados", value: formatNumber(summary.delayed_orders.value), context: `${formatPercentage(summary.delayed_orders.rate, false)} dos pedidos · ${delays.context}`, trend: delays.trend, path: "/operation/delays?days=30", investigationPath: "/investigations/delivery-delays?days=30" },
    { id: "tickets", label: "Chamados ativos", value: formatNumber(summary.open_tickets.value), context: "Abertos ou em andamento · toda a base", trend: { tone: "neutral", label: "Retrato atual" } },
  ];
}

export function buildChangeFeed(items = []) {
  // O endpoint traz comparativos, não eventos. Não atribuir “hoje”, horário ou
  // cronologia a estes sinais; o estoque é uma condição atual, sem série histórica.
  return items.map((item, index) => ({
    ...item,
    id: `${item.type}-${index}`,
    periodLabel: item.type === "inventory" ? "Condição da base" : "Entre os períodos",
    displayValue: item.type === "inventory"
      ? `${formatNumber(item.value)} combinações`
      : formatPercentage(item.value),
  }));
}

export function buildBranchRows(investigations = []) {
  // A API não publica ranking de todas as filiais. Lemos apenas evidências de
  // investigações ativas, sem inferir nomes do título nem criar scores por unidade.
  // Os labels fazem parte do payload atual; se mudarem, omitir a linha incompleta.
  return investigations.flatMap(({ alert, impact = [] }) => {
    const metric = (label, unit) => impact.find((item) => item.label === label && item.unit === unit)?.value;
    const name = metric("Filial", "text");
    const rate = metric("Taxa de atraso", "percentage");
    const overallRate = metric("Média geral", "percentage");
    const orders = metric("Pedidos recentes", "count");
    if (alert?.type !== "BRANCH_PERFORMANCE" || !name
      || !Number.isFinite(rate) || !Number.isFinite(overallRate)
      || !Number.isFinite(orders)) return [];
    return [{ key: alert.key, name, rate, overallRate, orders, severity: alert.severity }];
  });
}
