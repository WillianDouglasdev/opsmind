export const pipelineStatusLabels = {
  running: "Em execução",
  success: "Concluída",
  warning: "Concluída com rejeições",
  failed: "Falhou",
};

export const pipelineStepLabels = {
  extract: "Extract",
  validate: "Validate",
  transform: "Transform",
  load: "Load",
};

export function buildPipelineStages(run) {
  return Object.entries(pipelineStepLabels).map(([key, label]) => ({
    key,
    label,
    status: run?.steps?.[key]?.status ?? "pending",
    records: run?.steps?.[key]?.records ?? null,
  }));
}

export function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) return "Em andamento";
  return `${new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 3 }).format(seconds)}s`;
}
