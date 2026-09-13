import test from "node:test";
import assert from "node:assert/strict";
import { buildBranchRows, buildChangeFeed, buildIndicators } from "./dashboard.js";

test("indicadores aceitam Decimal serializado e mantêm ausência de comparação", () => {
  const summary = {
    revenue: { value: "1200.50", change_percentage: null },
    orders: { value: 10, change_percentage: 25 },
    delayed_orders: { value: 2, rate: 20, change_percentage: 50 },
    open_tickets: { value: 3 },
  };
  const before = structuredClone(summary);
  const indicators = buildIndicators(summary);
  assert.equal(indicators.length, 4);
  assert.match(indicators[0].value, /1\.201/);
  assert.equal(indicators[0].context, "Sem base de comparação");
  assert.deepEqual(indicators[0].trend, { tone: "neutral", label: "Sem comparação" });
  assert.deepEqual(indicators[1].trend, { tone: "positive", label: "Melhor" });
  assert.match(indicators[2].context, /20,0% dos pedidos/);
  assert.match(indicators[2].context, /\+50,0%/);
  assert.deepEqual(indicators[2].trend, { tone: "negative", label: "Pior" });
  assert.equal(indicators[3].context, "Abertos ou em andamento · toda a base");
  assert.deepEqual(indicators[3].trend, { tone: "neutral", label: "Retrato atual" });
  assert.deepEqual(summary, before);
});

test("comparativos respeitam se subir ou cair é favorável para cada indicador", () => {
  const indicators = buildIndicators({
    revenue: { value: 100, change_percentage: -5 },
    orders: { value: 10, change_percentage: 0 },
    delayed_orders: { value: 1, rate: 10, change_percentage: -25 },
    open_tickets: { value: 0 },
  });
  assert.deepEqual(indicators.map((indicator) => indicator.trend), [
    { tone: "negative", label: "Pior" },
    { tone: "neutral", label: "Estável" },
    { tone: "positive", label: "Melhor" },
    { tone: "neutral", label: "Retrato atual" },
  ]);
});

test("resumo ausente não fabrica indicadores zerados", () => {
  assert.deepEqual(buildIndicators(null), []);
});

test("feed diferencia comparação de período e snapshot, sem fabricar horários", () => {
  const items = [
    { type: "percentage", label: "Atrasos", value: null, direction: "neutral", description: "Sem base anterior" },
    { type: "inventory", label: "Estoque crítico", value: 4, direction: "current", description: "Quatro combinações abaixo do mínimo" },
  ];
  const feed = buildChangeFeed(items);
  assert.equal(feed[0].displayValue, "Sem base");
  assert.equal(feed[0].periodLabel, "Entre os períodos");
  assert.equal(feed[1].periodLabel, "Condição da base");
  assert.equal(feed[1].displayValue, "4 combinações");
  assert.equal(feed[1].description, items[1].description);
  assert.ok(feed.every((item) => !("timestamp" in item)));
  assert.deepEqual(buildChangeFeed(), []);
});

const branchInvestigation = {
  alert: { key: "branch-performance-contagem", type: "BRANCH_PERFORMANCE", severity: "high", title: "Título pode mudar" },
  impact: [
    { label: "Filial", unit: "text", value: "Contagem" },
    { label: "Taxa de atraso", unit: "percentage", value: 21.15 },
    { label: "Média geral", unit: "percentage", value: 13.92 },
    { label: "Pedidos recentes", unit: "count", value: 104 },
  ],
};

test("filial vem das evidências estruturadas, preservando taxas da API", () => {
  assert.deepEqual(buildBranchRows([branchInvestigation]), [{
    key: "branch-performance-contagem", name: "Contagem", rate: 21.15,
    overallRate: 13.92, orders: 104, severity: "high",
  }]);
});

test("ausência de alertas não cria filiais nem um ranking artificial", () => {
  assert.deepEqual(buildBranchRows(), []);
  assert.deepEqual(buildBranchRows([{ alert: { type: "INVENTORY_RISK" } }]), []);
});

test("evidência incompleta não vira taxa zero nem nome inferido do título", () => {
  assert.deepEqual(buildBranchRows([{ ...branchInvestigation, impact: branchInvestigation.impact.slice(1) }]), []);
});

test("unidade inesperada é rejeitada mesmo com o mesmo label", () => {
  const impact = branchInvestigation.impact.map((metric) => metric.label === "Taxa de atraso" ? { ...metric, unit: "count" } : metric);
  assert.deepEqual(buildBranchRows([{ ...branchInvestigation, impact }]), []);
});

test("valor numérico ausente não é convertido em percentual válido", () => {
  const impact = branchInvestigation.impact.map((metric) => metric.label === "Média geral" ? { ...metric, value: null } : metric);
  assert.deepEqual(buildBranchRows([{ ...branchInvestigation, impact }]), []);
});
