import test from "node:test";
import assert from "node:assert/strict";
import { buildPipelineStages, formatDuration, pipelineStatusLabels } from "./pipelines.js";
import { formatRelativeTime } from "./formatters.js";

test("etapas ausentes permanecem pendentes, sem inventar contagens", () => {
  assert.deepEqual(buildPipelineStages(null), [
    { key: "extract", label: "Extract", status: "pending", records: null },
    { key: "validate", label: "Validate", status: "pending", records: null },
    { key: "transform", label: "Transform", status: "pending", records: null },
    { key: "load", label: "Load", status: "pending", records: null },
  ]);
});

test("etapas usam somente o estado retornado pela API", () => {
  const stages = buildPipelineStages({ steps: { extract: { status: "success", records: 16 }, validate: { status: "warning", records: 12 } } });
  assert.equal(stages[0].records, 16);
  assert.equal(stages[1].status, "warning");
  assert.equal(stages[2].status, "pending");
});

test("duração e status têm apresentação determinística", () => {
  assert.match(formatDuration(0.018), /0,018s/);
  assert.equal(formatDuration(null), "Em andamento");
  assert.equal(pipelineStatusLabels.failed, "Falhou");
});

test("freshness é calculada a partir do timestamp real", () => {
  const now = new Date("2026-09-11T20:10:00Z");
  assert.match(formatRelativeTime("2026-09-11T20:06:00Z", now), /4 min/);
  assert.equal(formatRelativeTime(null, now), "Nunca executado");
});
