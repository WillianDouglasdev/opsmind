import assert from "node:assert/strict";
import { cwd } from "node:process";
import { after, before, test } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import react from "@vitejs/plugin-react";
import { createServer } from "vite";

import {
  investigationPath,
  investigationSearchParams,
  readInvestigationFilters,
} from "./investigations.js";

let server;
let InvestigationsList;
let DeliveryDelayInvestigation;

const filters = { days: 30, branch: "7" };
const evidence = [
  {
    key: "delay-rate", type: "delivery", title: "Taxa de atraso da filial",
    description: "Comparação equivalente.", importance: "primary", source: "Pedidos",
    current: { label: "Atual", value: 21.15, unit: "percentage" },
    comparison: { label: "Anterior", value: 11.4, unit: "percentage" },
    detail_url: "/operation/branches/7?days=30&delivery=late",
  },
  {
    key: "tickets", type: "tickets", title: "Chamados relacionados à entrega",
    description: "Sinal simultâneo, sem causalidade.", importance: "related", source: "Chamados",
    current: { label: "Atual", value: 8, unit: "count" },
    comparison: { label: "Anterior", value: 3, unit: "count" }, detail_url: null,
  },
];
const detail = {
  data_status: "complete",
  period: { days: 30 },
  summary: {
    title: "Aumento de atrasos em Contagem", situation: "Acima da média operacional.",
    severity: "high", branch: { id: 7, name: "Contagem" }, branch_delay_rate: 21.15,
    operation_delay_rate: 11.4, difference_percentage_points: 9.75,
    previous_delay_rate: 12, delayed_orders: 9, impacted_customers: 6,
    affected_revenue: "12500.00",
  },
  evidence,
  timeline: [{ date: "2026-08-20", type: "delayed_orders", title: "Pedidos atrasados registrados", description: "2 de 5 pedidos.", value: 2, unit: "count", source: "Pedidos", detail_url: "/operation/branches/7?days=30&delivery=late" }],
  next_steps: [{ key: "review", title: "Revisar pedidos", description: "Abrir o recorte.", detail_url: "/operation/branches/7?days=30&delivery=late" }],
  causality_notice: "As evidências não confirmam relações de causa e efeito.",
  navigation: { investigations_url: "/investigations?days=30", operation_url: "/operation/branches/7?days=30&delivery=late" },
};

function render(Component, props, theme = "light") {
  return renderToStaticMarkup(
    React.createElement(MemoryRouter, null,
      React.createElement("div", { "data-theme": theme }, React.createElement(Component, props))),
  );
}

before(async () => {
  server = await createServer({
    root: cwd(), configFile: false, appType: "custom",
    server: { middlewareMode: true, hmr: { port: 24679 } }, plugins: [react()],
  });
  ({ InvestigationsList } = await server.ssrLoadModule("/src/pages/InvestigationsPage.jsx"));
  ({ DeliveryDelayInvestigation } = await server.ssrLoadModule("/src/pages/DeliveryDelayInvestigationPage.jsx"));
});

after(async () => server?.close());

test("query string preserva período e filial", () => {
  assert.deepEqual(readInvestigationFilters(new URLSearchParams("days=90&branch=7")), { days: 90, branch: "7" });
  assert.equal(investigationSearchParams(filters, { days: 7 }).toString(), "days=7&branch=7");
  assert.equal(investigationPath(filters), "/investigations/delivery-delays?days=30&branch=7");
});

test("lista apresenta somente a investigação funcional e seu contexto", () => {
  const state = { status: "success", data: { items: [{ key: "delivery-delays", type: "delivery_delays", title: "Atrasos de entrega", description: "Fatos relacionados.", severity: "high", branch: { id: 7, name: "Contagem" }, delay_rate: 21.15, delayed_orders: 9, detail_url: investigationPath(filters) }] } };
  const html = render(InvestigationsList, { state, filters, onPeriodChange() {} });
  assert.match(html, /Atrasos de entrega/);
  assert.match(html, /Contagem/);
  assert.match(html, /href="\/investigations\/delivery-delays\?days=30&amp;branch=7"/);
});

test("lista diferencia loading, erro e ausência válida", () => {
  assert.match(render(InvestigationsList, { state: { status: "loading" }, filters }), /Reunindo investigações/);
  assert.match(render(InvestigationsList, { state: { status: "error" }, filters }), /Não foi possível carregar/);
  assert.match(render(InvestigationsList, { state: { status: "success", data: { items: [] } }, filters, onPeriodChange() {} }), /Nenhuma investigação disponível/);
});

test("detalhe apresenta resumo, evidências, timeline e próximos passos", () => {
  const html = render(DeliveryDelayInvestigation, { state: { status: "success", data: detail }, filters, onPeriodChange() {} });
  assert.match(html, /Aumento de atrasos em Contagem/);
  assert.match(html, /Taxa de atraso da filial/);
  assert.match(html, /Chamados relacionados à entrega/);
  assert.match(html, /Dias com pedidos atrasados/);
  assert.match(html, /Sugestões baseadas em regras/);
  assert.match(html, /Correlação não é causalidade/);
});

test("detalhe trata loading, erro, vazio e dados incompletos", () => {
  assert.match(render(DeliveryDelayInvestigation, { state: { status: "loading" }, filters }), /Organizando as evidências/);
  assert.match(render(DeliveryDelayInvestigation, { state: { status: "error", error: { status: 500 } }, filters }), /Não foi possível carregar/);
  assert.match(render(DeliveryDelayInvestigation, { state: { status: "success", data: { ...detail, data_status: "empty", summary: null } }, filters, onPeriodChange() {} }), /Nenhum atraso para investigar/);
  assert.match(render(DeliveryDelayInvestigation, { state: { status: "success", data: { ...detail, data_status: "partial", evidence: evidence.slice(0, 1) } }, filters, onPeriodChange() {} }), /Dados incompletos/);
});

test("workspace mantém conteúdo nos temas claro e escuro", () => {
  for (const theme of ["light", "dark"]) {
    const html = render(DeliveryDelayInvestigation, { state: { status: "success", data: detail }, filters, onPeriodChange() {} }, theme);
    assert.match(html, new RegExp(`data-theme="${theme}"`));
    assert.match(html, /Fatos relacionados ao problema/);
  }
});
