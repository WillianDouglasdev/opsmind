import assert from "node:assert/strict";
import test from "node:test";
import { buildAlertSegments, buildBranchDelaySegments, buildQualitySegments, qualitySegmentLabel, readChartPalette } from "./charts.js";
import {
  applyTheme,
  getInitialTheme,
  oppositeTheme,
  persistTheme,
  resolveTheme,
  themeControlLabel,
} from "./theme.js";

test("tema salvo prevalece e preferência do sistema cobre primeira visita", () => {
  assert.equal(resolveTheme("light", true), "light");
  assert.equal(resolveTheme("dark", false), "dark");
  assert.equal(resolveTheme(null, true), "dark");
  assert.equal(resolveTheme("inválido", false), "light");
});

test("leitura do tema tolera armazenamento indisponível", () => {
  const failingStorage = { getItem() { throw new Error("bloqueado"); } };
  assert.equal(getInitialTheme({ storage: failingStorage, mediaQuery: { matches: true } }), "dark");
  assert.equal(getInitialTheme({ storage: { getItem: () => "light" }, mediaQuery: { matches: true } }), "light");
});

test("aplicação e persistência atualizam documento sem depender do React", () => {
  const root = { dataset: {}, style: {} };
  const meta = { setAttribute(name, value) { this[name] = value; } };
  const writes = [];
  const storage = { setItem: (...args) => writes.push(args) };
  assert.equal(applyTheme("dark", { root, meta }), "dark");
  assert.equal(root.dataset.theme, "dark");
  assert.equal(root.style.colorScheme, "dark");
  assert.equal(meta.content, "#0c1628");
  assert.equal(persistTheme("dark", storage), true);
  assert.deepEqual(writes, [["opsmind-theme", "dark"]]);
});

test("controle anuncia a ação e alterna entre os dois temas", () => {
  assert.equal(oppositeTheme("light"), "dark");
  assert.equal(oppositeTheme("dark"), "light");
  assert.equal(themeControlLabel("light"), "Ativar tema escuro");
  assert.equal(themeControlLabel("dark"), "Ativar tema claro");
});

test("paleta de gráficos e donut usam tokens e percentuais legíveis", () => {
  const values = {
    "--chart-primary": "#primary", "--chart-success": "#success",
    "--chart-warning": "#warning", "--chart-danger": "#danger",
    "--chart-info": "#info", "--chart-grid": "#grid", "--chart-label": "#label",
    "--chart-tooltip-background": "#tooltip", "--chart-tooltip-text": "#tooltip-text",
    "--surface": "#surface", "--font-body": "Inter",
  };
  const palette = readChartPalette({ getPropertyValue: (name) => ` ${values[name]} ` });
  assert.equal(palette.grid, "#grid");
  assert.equal(palette.tooltipText, "#tooltip-text");
  assert.equal(palette.categories.length, 5);
  const segments = buildQualitySegments({ records_received: 16, records_valid: 12, records_rejected: 4, quality_percentage: 75 });
  assert.deepEqual(segments.map(({ label, value, percentage }) => ({ label, value, percentage })), [
    { label: "Válidos", value: 12, percentage: 75 },
    { label: "Rejeitados", value: 4, percentage: 25 },
  ]);
  assert.match(qualitySegmentLabel(segments[0]), /12 · 75,0%/);
  assert.deepEqual(buildQualitySegments({ records_received: 0 }), []);
});

test("rosca agrupa alertas por severidade sem inventar fatias vazias", () => {
  const segments = buildAlertSegments(["high", "critical", "high", "low", "medium"].map((severity) => ({ severity })));
  assert.deepEqual(segments.map(({ key, value }) => [key, value]), [["critical", 1], ["high", 2], ["medium", 1], ["low", 1]]);
  assert.equal(segments[0].tone, "danger");
  assert.deepEqual(buildAlertSegments(), []);
  assert.deepEqual(buildAlertSegments([{ severity: "high" }]).map(({ key }) => key), ["high"]);
});

test("pizza usa contagens de todas as filiais e preserva os links do recorte", () => {
  const branches = [5, 2, 4, 1, 3].map((id) => ({ id, name: `Filial ${id}`, delayed_orders: id, delay_rate: 90 }));
  const segments = buildBranchDelaySegments(branches);
  assert.equal(segments.length, 5);
  assert.equal(segments.reduce((sum, segment) => sum + segment.value, 0), 15);
  assert.deepEqual(segments.map(({ key }) => key), [1, 2, 3, 4, 5]);
  assert.equal(segments[1].href, "/operation/branches/2?days=30&delivery=late");
  assert.deepEqual(branches.map(({ id }) => id), [5, 2, 4, 1, 3]);
  assert.deepEqual(buildBranchDelaySegments([...branches].reverse()), segments);
});

test("pizza omite zeros e dados incompletos sem substituir contagens por taxas", () => {
  assert.deepEqual(buildBranchDelaySegments(), []);
  assert.deepEqual(buildBranchDelaySegments([{ id: 1, delayed_orders: 0 }]), []);
  assert.deepEqual(buildBranchDelaySegments([{ id: 1, delay_rate: 20 }]), []);
  assert.deepEqual(buildBranchDelaySegments([{ id: 1, delayed_orders: -1 }]), []);
});
