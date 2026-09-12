import { ArrowRight, Database } from "lucide-react";
import { Link } from "react-router-dom";
import { demoMetadata } from "../../data/demoMetadata.js";
import { formatDate, formatDateTime, formatNumber, formatPercentage, formatRelativeTime } from "../../utils/formatters.js";
import { buildPipelineStages, pipelineStatusLabels } from "../../utils/pipelines.js";
import SectionState from "../common/SectionState.jsx";
import DataQualityDonut from "../charts/DataQualityDonut.jsx";

export default function DataFlow({ referenceDate, section, onRetry }) {
  const pipeline = section.data;
  const run = pipeline?.latest_run;
  const stages = buildPipelineStages(run);
  return (
    <section className="data-flow" aria-labelledby="data-flow-title">
      <div className="section-heading"><h2 id="data-flow-title">Dados da operação</h2><Database size={17} aria-hidden="true" /></div>
      <p className="section-description">Origem e publicação dos pedidos usados pelos indicadores.</p>
      {section.status !== "success" ? <SectionState status={section.status} onRetry={onRetry} />
        : !run ? <>
          <div className="pipeline-never"><strong>Nunca executado</strong><p>A fonte demonstrativa ainda não foi publicada pela pipeline.</p></div>
          <dl className="data-metadata"><div><dt>Referência dos indicadores</dt><dd>{referenceDate ? formatDate(referenceDate) : "Indisponível"}</dd></div></dl>
        </> : <>
          <div className={`pipeline-inline-status ${run.status}`}><span>{pipelineStatusLabels[run.status]}</span><small>Execução #{run.id}</small></div>
          <DataQualityDonut run={run} compact />
          <ol className="data-flow-stages" aria-label="Etapas da última execução">
            {stages.map((stage, index) => (
              <li className={stage.status} key={stage.key}><span className="flow-step-number">0{index + 1}</span><span>{stage.label}</span>{index < stages.length - 1 && <ArrowRight size={13} aria-hidden="true" />}</li>
            ))}
          </ol>
          <dl className="data-metadata">
            <div><dt>Fonte</dt><dd>{run.source_name}</dd></div>
            <div><dt>Última publicação</dt><dd>{pipeline.last_published_at ? <><time dateTime={pipeline.last_published_at}>{formatDateTime(pipeline.last_published_at)}</time><small>{formatRelativeTime(pipeline.last_published_at)}</small></> : "Nunca publicada"}</dd></div>
            <div><dt>Qualidade</dt><dd>{formatPercentage(run.quality_percentage, false)}</dd></div>
            <div><dt>Resultado</dt><dd>{formatNumber(run.records_loaded)} carregados · {formatNumber(run.records_rejected)} rejeitados</dd></div>
          </dl>
        </>}
      <div className="pipeline-note"><span className="demo-tag">{demoMetadata.label}</span><p>{demoMetadata.source}. <Link to="/pipelines">Ver monitoramento</Link></p></div>
    </section>
  );
}
