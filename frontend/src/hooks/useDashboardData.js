import { useCallback, useEffect, useState } from "react";
import { getAlerts, getDashboardChanges, getDashboardSummary, getDashboardTrends, getOperationOverview, getPipeline } from "../services/api.js";

const initialSections = () => Object.fromEntries(
  ["summary", "trends", "changes", "alerts", "branches", "pipeline"].map((key) => [key, { status: "loading", data: null }]),
);

export default function useDashboardData() {
  const [sections, setSections] = useState(initialSections);
  const [revision, setRevision] = useState(0);
  const [consultedAt, setConsultedAt] = useState(null);

  // A atualização descarta o retrato anterior. O cleanup cancela toda a rodada,
  // evitando que respostas atrasadas sobrescrevam uma consulta mais recente.
  const refresh = useCallback(() => {
    setSections(initialSections());
    setConsultedAt(null);
    setRevision((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    const publish = (key, state) => {
      if (!controller.signal.aborted) setSections((current) => ({ ...current, [key]: state }));
    };
    const fail = (key, error) => {
      if (controller.signal.aborted) return;
      if (import.meta.env.DEV) console.error(`[OpsMind] Falha ao carregar ${key}`, error);
      publish(key, { status: "error", data: null });
    };
    async function load(key, fetchData) {
      try {
        const data = await fetchData(options);
        publish(key, { status: "success", data });
        if (key === "summary" && !controller.signal.aborted) setConsultedAt(new Date());
      } catch (error) { fail(key, error); }
    }

    // Seções independentes: falha do gráfico não esconde saúde ou prioridades.
    // Isso não garante snapshot transacional; a referência segue vindo do backend.
    load("summary", getDashboardSummary);
    load("trends", getDashboardTrends);
    load("changes", getDashboardChanges);
    load("pipeline", (requestOptions) => getPipeline("orders", requestOptions));
    load("branches", (requestOptions) => getOperationOverview(30, requestOptions));
    async function loadAlerts() {
      try {
        const alerts = await getAlerts(options);
        if (controller.signal.aborted) return;
        publish("alerts", { status: "success", data: alerts });
      } catch (error) {
        fail("alerts", error);
      }
    }
    loadAlerts();
    return () => controller.abort();
  }, [revision]);

  return { sections, consultedAt, refresh, loading: Object.values(sections).some((section) => section.status === "loading") };
}
