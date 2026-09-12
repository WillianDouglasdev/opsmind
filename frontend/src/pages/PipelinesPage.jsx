import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Check, Circle, Clock3, Database, RefreshCw, X } from "lucide-react";
import SectionState from "../components/common/SectionState.jsx";
import DataQualityDonut from "../components/charts/DataQualityDonut.jsx";
import { getPipeline, getPipelineRun } from "../services/api.js";
import { formatDateTime, formatNumber, formatPercentage, formatRelativeTime } from "../utils/formatters.js";
import { buildPipelineStages, formatDuration, pipelineStatusLabels } from "../utils/pipelines.js";

function StepIcon({ status }) {
  if (status === "success") return <Check aria-hidden="true" />;
  if (status === "warning") return <AlertTriangle aria-hidden="true" />;
  if (status === "failed") return <X aria-hidden="true" />;
  if (status === "running") return <RefreshCw className="spin" aria-hidden="true" />;
  return <Circle aria-hidden="true" />;
}

export default function PipelinesPage() {
  const [state, setState] = useState({ status: "loading", data: null });
  const [selectedRun, setSelectedRun] = useState({ status: "idle", data: null });

  const load = useCallback((signal) => {
    getPipeline("orders", { signal }).then((data) => {
      if (!signal?.aborted) setState({ status: "success", data });
    }).catch((error) => {
      if (!signal?.aborted) {
        setState({ status: "error", data: null });
        if (import.meta.env.DEV) console.error("[OpsMind] Monitoramento de pipelines indisponível", error);
      }
    });
  }, []);

  function retry() {
    setState({ status: "loading", data: null });
    load();
  }

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function showRun(runId) {
    setSelectedRun({ status: "loading", data: null });
    try {
      setSelectedRun({ status: "success", data: await getPipelineRun("orders", runId) });
    } catch (error) {
      setSelectedRun({ status: "error", data: null });
      if (import.meta.env.DEV) console.error("[OpsMind] Detalhe da execução indisponível", error);
    }
  }

  if (state.status !== "success") {
    return <section className="pipelines-page-state"><SectionState status={state.status} title={state.status === "loading" ? "Consultando execuções…" : undefined} onRetry={retry} /></section>;
  }

  const pipeline = state.data;
  const run = pipeline.latest_run;
  if (!run) {
    return <section className="pipeline-empty" aria-labelledby="pipeline-empty-title"><Database size={24} aria-hidden="true" /><h2 id="pipeline-empty-title">Pipeline nunca executada</h2><p>Prepare a base operacional e execute o comando de pedidos para iniciar o histórico.</p><code>python manage.py run_data_pipeline orders</code></section>;
  }

  const stages = buildPipelineStages(run);
  return (
    <div className="pipelines-page">
      <section className="pipeline-overview" aria-labelledby="orders-pipeline-title">
        <div className="pipeline-overview-heading">
          <div><p className="eyebrow">Exportação demonstrativa de ERP</p><h2 id="orders-pipeline-title">{pipeline.name}</h2><p>{pipeline.description}</p></div>
          <div className={`pipeline-current-status ${run.status}`}><span>{pipelineStatusLabels[run.status]}</span><small>Execução #{run.id}</small></div>
        </div>

        <ol className="pipeline-steps" aria-label="Etapas da última execução">
          {stages.map((stage) => <li className={stage.status} key={stage.key}><StepIcon status={stage.status} /><div><strong>{stage.label}</strong><small>{stage.records === null ? pipelineStatusLabels[stage.status] ?? "Aguardando" : `${formatNumber(stage.records)} registros`}</small></div></li>)}
        </ol>

        <dl className="pipeline-counts">
          <div><dt>Recebidos</dt><dd>{formatNumber(run.records_received)}</dd></div>
          <div><dt>Válidos</dt><dd>{formatNumber(run.records_valid)}</dd></div>
          <div><dt>Rejeitados</dt><dd>{formatNumber(run.records_rejected)}</dd></div>
          <div><dt>Carregados</dt><dd>{formatNumber(run.records_loaded)}</dd></div>
        </dl>

        <div className="pipeline-publication">
          <div className="pipeline-quality-visual"><span>Qualidade · válidos ÷ recebidos</span><DataQualityDonut run={run} /></div>
          <dl>
            <div><dt>Última execução</dt><dd><time dateTime={run.started_at}>{formatDateTime(run.started_at)}</time></dd></div>
            <div><dt>Última publicação</dt><dd>{pipeline.last_published_at ? `${formatDateTime(pipeline.last_published_at)} · ${formatRelativeTime(pipeline.last_published_at)}` : "Nunca publicada"}</dd></div>
            <div><dt>Duração</dt><dd>{formatDuration(run.duration_seconds)}</dd></div>
            <div><dt>Fonte</dt><dd>{run.source_name}</dd></div>
          </dl>
        </div>
        {run.error_message && <p className="pipeline-error" role="alert">{run.error_message}</p>}
      </section>

      <section className="pipeline-history" aria-labelledby="pipeline-history-title">
        <div className="section-heading"><div><h2 id="pipeline-history-title">Histórico recente</h2><p className="section-description">As dez execuções mais recentes da pipeline de pedidos.</p></div><button className="quiet-button" type="button" onClick={() => load()}><RefreshCw size={14} aria-hidden="true" /> Atualizar</button></div>
        <div className="pipeline-history-table"><table><caption>Execuções recentes de pedidos</caption><thead><tr><th scope="col">Execução</th><th scope="col">Status</th><th scope="col">Início</th><th scope="col">Qualidade</th><th scope="col">Duração</th><th scope="col"><span className="visually-hidden">Detalhes</span></th></tr></thead><tbody>{pipeline.recent_runs.map((item) => <tr key={item.id}><th scope="row">#{item.id}</th><td><span className={`pipeline-status-label ${item.status}`}>{pipelineStatusLabels[item.status]}</span></td><td>{formatDateTime(item.started_at)}</td><td>{formatPercentage(item.quality_percentage, false)}</td><td>{formatDuration(item.duration_seconds)}</td><td><button type="button" className="text-button" onClick={() => showRun(item.id)}>Ver detalhes</button></td></tr>)}</tbody></table></div>
      </section>

      {selectedRun.status !== "idle" && <section className="pipeline-run-detail" aria-labelledby={selectedRun.status === "success" ? "run-detail-title" : undefined} aria-label={selectedRun.status === "success" ? undefined : "Detalhes da execução"}>
        {selectedRun.status !== "success" ? <SectionState status={selectedRun.status} /> : <>
          <div className="section-heading"><div><p className="eyebrow">Execução #{selectedRun.data.id}</p><h2 id="run-detail-title">Registros rejeitados</h2></div><button className="text-button" type="button" onClick={() => setSelectedRun({ status: "idle", data: null })}>Fechar</button></div>
          {selectedRun.data.issues.length ? <ul className="pipeline-issues">{selectedRun.data.issues.map((issue, index) => <li key={`${issue.record_identifier}-${index}`}><strong>{issue.record_identifier}</strong><p>{issue.message}</p><small>{issue.code} · detectado em {formatDateTime(issue.detected_at)}</small></li>)}</ul> : <p className="pipeline-no-issues"><Check size={16} aria-hidden="true" /> Nenhum registro foi rejeitado nesta execução.</p>}
        </>}
      </section>}

      <footer className="pipeline-command-note"><Clock3 size={16} aria-hidden="true" /><p>A execução continua deliberadamente manual nesta fase. O frontend apenas consulta o resultado persistido.</p></footer>
    </div>
  );
}
