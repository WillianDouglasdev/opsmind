import logging
import time
from pathlib import Path

from django.utils import timezone

from operations.ingestion.extract import ExtractionError, extract_orders
from operations.ingestion.load import load_orders
from operations.ingestion.transform import transform_orders
from operations.ingestion.validate import validate_orders
from operations.models import PipelineIssue, PipelineRun

STEP_KEYS = ("extract", "validate", "transform", "load")
logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    def __init__(self, run: PipelineRun):
        self.run = run
        super().__init__(run.error_message)


def _initial_steps() -> dict:
    return {key: {"status": "pending", "records": None} for key in STEP_KEYS}


def _save_step(run: PipelineRun, key: str, status: str, records=None) -> None:
    run.steps = {**run.steps, key: {"status": status, "records": records}}
    run.save(update_fields=["steps"])


def run_orders_pipeline(source_path: Path) -> PipelineRun:
    source_path = Path(source_path)
    run = PipelineRun.objects.create(
        pipeline_key=PipelineRun.Pipeline.ORDERS,
        source_name=source_path.name,
        steps=_initial_steps(),
    )
    started = time.perf_counter()
    active_step = "extract"
    try:
        _save_step(run, active_step, "running")
        raw_records = extract_orders(source_path)
        run.records_received = len(raw_records)
        run.save(update_fields=["records_received"])
        _save_step(run, active_step, "success", len(raw_records))

        active_step = "validate"
        _save_step(run, active_step, "running")
        valid_records, rejected = validate_orders(raw_records)
        run.records_valid = len(valid_records)
        run.records_rejected = len(rejected)
        run.save(update_fields=["records_valid", "records_rejected"])
        PipelineIssue.objects.bulk_create([
            PipelineIssue(
                run=run,
                record_identifier=item.record_identifier,
                code=item.code,
                message=item.message,
            )
            for item in rejected
        ])
        _save_step(run, active_step, "warning" if rejected else "success", len(valid_records))

        active_step = "transform"
        _save_step(run, active_step, "running")
        clean_orders = transform_orders(valid_records)
        _save_step(run, active_step, "success", len(clean_orders))

        active_step = "load"
        _save_step(run, active_step, "running")
        run.records_loaded = load_orders(clean_orders)
        run.published_at = timezone.now()
        run.save(update_fields=["records_loaded", "published_at"])
        _save_step(run, active_step, "success", run.records_loaded)
        run.status = PipelineRun.Status.WARNING if rejected else PipelineRun.Status.SUCCESS
    except Exception as error:
        logger.exception("[OpsMind] Falha na etapa %s da pipeline de pedidos", active_step)
        _save_step(run, active_step, "failed")
        run.status = PipelineRun.Status.FAILED
        # Erros de fonte já são sanitizados. Exceções internas ficam apenas no log;
        # a persistência e a API não expõem SQL, caminhos ou traceback.
        run.error_message = (
            str(error) if isinstance(error, ExtractionError)
            else f"Falha durante a etapa {active_step}."
        )
    finally:
        run.finished_at = timezone.now()
        run.duration_ms = max(0, round((time.perf_counter() - started) * 1000))
        run.save(update_fields=["status", "error_message", "finished_at", "duration_ms"])

    if run.status == PipelineRun.Status.FAILED:
        raise PipelineExecutionError(run)
    return run
