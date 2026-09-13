import assert from "node:assert/strict";
import { cwd } from "node:process";
import { after, before, test } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import react from "@vitejs/plugin-react";
import { createServer } from "vite";

import { operationPath, operationSearchParams, readOperationFilters } from "./operation.js";
import { buildBranchDelaySegments } from "./charts.js";

let server;
let OperationOverview;
let OrderFilters;
let OrderTable;
let BranchComparison;
let DataQualityDonut;
let DistributionChart;
let AlertPreview;
let BranchPerformance;
let HealthScore;
let SiteFooter;
let KpiCard;

const filters = { days: 30, branch: "", status: "", delivery: "all", page: 1 };
const overview = {
  period: { start_date: "2026-07-31", end_date: "2026-08-29" },
  metrics: { orders: 20, delayed_orders: 4, delay_rate: 20, revenue: "5000.00", customers: 8, active_tickets: 3, critical_inventory: 1 },
  branch_average: { delay_rate: 10 },
  branches: [{ id: 7, name: "Contagem", city: "Contagem", state: "MG", orders: 10, delayed_orders: 4, delay_rate: 40, revenue: "3000.00", active_tickets: 2, health: { score: 64, status: "Risco moderado" } }],
  attention: { worst_branch: { id: 7, name: "Contagem", delayed_orders: 4, delay_rate: 40 }, critical_products: [], strategic_customers_impacted: 2 },
};

function render(Component, props) {
  return renderToStaticMarkup(React.createElement(MemoryRouter, null, React.createElement(Component, props)));
}

before(async () => {
  server = await createServer({
    root: cwd(), configFile: false, appType: "custom",
    optimizeDeps: { noDiscovery: true },
    server: { middlewareMode: true }, plugins: [react()],
  });
  ({ OperationOverview } = await server.ssrLoadModule("/src/pages/OperationPage.jsx"));
  ({ default: OrderFilters } = await server.ssrLoadModule("/src/components/operation/OrderFilters.jsx"));
  ({ default: OrderTable } = await server.ssrLoadModule("/src/components/operation/OrderTable.jsx"));
  ({ default: BranchComparison } = await server.ssrLoadModule("/src/components/operation/BranchComparison.jsx"));
  ({ default: DataQualityDonut } = await server.ssrLoadModule("/src/components/charts/DataQualityDonut.jsx"));
  ({ default: DistributionChart } = await server.ssrLoadModule("/src/components/charts/DistributionChart.jsx"));
  ({ default: AlertPreview } = await server.ssrLoadModule("/src/components/dashboard/AlertPreview.jsx"));
  ({ default: BranchPerformance } = await server.ssrLoadModule("/src/components/dashboard/BranchPerformance.jsx"));
  ({ default: HealthScore } = await server.ssrLoadModule("/src/components/dashboard/HealthScore.jsx"));
  ({ default: SiteFooter } = await server.ssrLoadModule("/src/components/layout/SiteFooter.jsx"));
  ({ default: KpiCard } = await server.ssrLoadModule("/src/components/dashboard/KpiCard.jsx"));
});

after(async () => server?.close());

test("saúde operacional usa indicador circular com percentual acessível", () => {
  const html = render(HealthScore, { health: { score: 69, status: "Risco moderado", description: "Atrasos exigem atenção.", components: [] } });
  assert.match(html, /class="health-gauge"/);
  assert.match(html, /role="meter"/);
  assert.match(html, /aria-valuenow="69"/);
  assert.match(html, /<strong>69<span>%<\/span><\/strong>/);
  assert.doesNotMatch(html, /health-track/);
});

test("rodapé identifica o responsável e aponta para seu LinkedIn", () => {
  const html = render(SiteFooter);
  assert.match(html, /Responsável pelo projeto/);
  assert.match(html, /Willian Douglas/);
  assert.match(html, /https:\/\/www\.linkedin\.com\/in\/willian-douglas-contato/);
  assert.match(html, /target="_blank"/);
});

test("indicador apresenta tendência por cor e também por texto", () => {
  const html = render(KpiCard, { metric: { id: "delays", label: "Pedidos atrasados", value: "60", context: "+24,2% vs. período anterior", trend: { tone: "negative", label: "Pior" } } });
  assert.match(html, /indicator-trend negative/);
  assert.match(html, />Pior<\/small>/);
  assert.match(html, /\+24,2% vs\. período anterior/);
});

test("pizza preserva legenda textual, quantidades, percentuais e links", () => {
  const html = render(DistributionChart, { variant: "pie", segments: buildBranchDelaySegments(overview.branches), label: "Pedidos atrasados por filial" });
  assert.match(html, /Pedidos atrasados por filial/);
  assert.match(html, /Contagem/);
  assert.match(html, /<strong>4<\/strong>/);
  assert.match(html, /100,0%/);
  assert.match(html, /href="\/operation\/branches\/7\?days=30&amp;delivery=late"/);
  assert.equal(render(DistributionChart, { segments: [], label: "Sem dados" }), "");
});

test("painel de alertas mostra severidade e diferencia vazio de erro", () => {
  const html = render(AlertPreview, { section: { status: "success", data: [
    { key: "critical", title: "Atrasos", severity: "critical" },
    { key: "high", title: "Estoque", severity: "high" },
  ] } });
  assert.match(html, /Alertas por severidade/);
  assert.match(html, /Críticos/);
  assert.match(html, /50,0%/);
  assert.match(html, /href="\/alerts\/critical"/);
  const empty = render(AlertPreview, { section: { status: "success", data: [] } });
  assert.match(empty, /Nenhum alerta ativo/);
  assert.doesNotMatch(empty, /distribution-chart/);
  assert.doesNotMatch(render(AlertPreview, { section: { status: "error" } }), /Nenhum alerta ativo|distribution-chart/);
});

test("dashboard mantém taxa da filial separada da participação na pizza", () => {
  const html = render(BranchPerformance, { section: { status: "success", data: overview } });
  assert.match(html, /40,0%/);
  assert.match(html, /100,0%/);
  assert.match(html, /Pedidos atrasados por filial/);
  assert.doesNotMatch(render(BranchPerformance, { section: { status: "loading" } }), /distribution-chart/);
  assert.doesNotMatch(render(BranchPerformance, { section: { status: "success", data: { ...overview, branches: [] } } }), /distribution-chart/);
});

test("filtros são lidos e serializados de forma previsível", () => {
  assert.deepEqual(readOperationFilters(new URLSearchParams("days=90&branch=2&status=delayed&delivery=late&page=3")), {
    days: 90, branch: "2", status: "delayed", delivery: "late", page: 3,
  });
  assert.equal(operationSearchParams(filters, { status: "delayed", page: 8 }).toString(), "days=30&status=delayed&page=8");
  assert.equal(operationSearchParams({ ...filters, page: 4 }, { delivery: "late" }).toString(), "days=30&delivery=late");
  assert.equal(operationPath("/operation/branches/7", filters), "/operation/branches/7?days=30");
});

test("visão da Operação renderiza métricas e navegação para filial", () => {
  const html = render(OperationOverview, { state: { status: "success", data: overview }, filters, onPeriodChange() {} });
  assert.match(html, /Filiais/);
  assert.match(html, /20,0%/);
  assert.match(html, /href="\/operation\/branches\/7\?days=30"/);
  assert.match(html, /Pontos de atenção/);
});

test("visão da Operação diferencia loading, erro e vazio", () => {
  assert.match(render(OperationOverview, { state: { status: "loading" }, filters }), /Organizando a visão da operação/);
  assert.match(render(OperationOverview, { state: { status: "error" }, filters }), /Não foi possível carregar/);
  const empty = { ...overview, branches: [], attention: { ...overview.attention, worst_branch: null } };
  assert.match(render(OperationOverview, { state: { status: "success", data: empty }, filters, onPeriodChange() {} }), /Nenhuma filial cadastrada/);
});

test("filtros renderizam valores selecionados e filiais disponíveis", () => {
  const html = render(OrderFilters, { filters: { ...filters, branch: "7", delivery: "late" }, branches: overview.branches, onChange() {} });
  assert.match(html, /Filial/);
  assert.match(html, /Contagem/);
  assert.match(html, /Atrasados no KPI/);
  assert.match(html, /value="late" selected=""/);
});

test("pedidos tratam vazio sem transformar ausência em erro", () => {
  const html = render(OrderTable, { state: { status: "success", data: { results: [], count: 0, page: 1, total_pages: 1 } }, page: 1, onPageChange() {} });
  assert.match(html, /Nenhum pedido neste recorte/);
});

test("comparação de filial apresenta unidade, média e diferença do backend", () => {
  const html = render(BranchComparison, { scope: "Média das filiais", comparisons: [{ key: "delay_rate", label: "Atrasos", unit: "percentage", branch_value: 21.15, average_value: 11.4, difference: 9.75 }] });
  assert.match(html, /21,2%/);
  assert.match(html, /média 11,4%/);
  assert.match(html, /\+9,8%/);
});

test("donut de qualidade mantém valores e percentuais disponíveis em texto", () => {
  const html = render(DataQualityDonut, { run: { records_received: 16, records_valid: 12, records_rejected: 4, quality_percentage: 75 } });
  assert.match(html, /Distribuição da qualidade/);
  assert.match(html, /Válidos/);
  assert.match(html, /Rejeitados/);
  assert.match(html, /75,0%/);
});
