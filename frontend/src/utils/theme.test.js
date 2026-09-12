import assert from "node:assert/strict";
import test from "node:test";
import { buildQualitySegments, qualitySegmentLabel, readChartPalette } from "./charts.js";
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
  assert.equal(meta.content, "#111714");
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
  const segments = buildQualitySegments({ records_received: 16, records_valid: 12, records_rejected: 4, quality_percentage: 75 });
  assert.deepEqual(segments.map(({ label, value, percentage }) => ({ label, value, percentage })), [
    { label: "Válidos", value: 12, percentage: 75 },
    { label: "Rejeitados", value: 4, percentage: 25 },
  ]);
  assert.match(qualitySegmentLabel(segments[0]), /12 · 75,0%/);
  assert.deepEqual(buildQualitySegments({ records_received: 0 }), []);
});
