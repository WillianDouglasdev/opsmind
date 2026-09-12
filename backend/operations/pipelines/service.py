from operations.models import PipelineRun

PIPELINES = {
    PipelineRun.Pipeline.ORDERS: {
        "name": "Pedidos",
        "description": "Exportação demonstrativa do ERP para a base operacional.",
    }
}


def _run_payload(run: PipelineRun, include_issues: bool = False) -> dict:
    payload = {
        "id": run.pk,
        "pipeline_key": run.pipeline_key,
        "status": run.status,
        "source_name": run.source_name,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "published_at": run.published_at,
        "duration_seconds": round(run.duration_ms / 1000, 3) if run.duration_ms is not None else None,
        "records_received": run.records_received,
        "records_valid": run.records_valid,
        "records_rejected": run.records_rejected,
        "records_loaded": run.records_loaded,
        "quality_percentage": run.quality_percentage,
        "steps": run.steps,
        "error_message": run.error_message,
    }
    if include_issues:
        payload["issues"] = [
            {
                "record_identifier": issue.record_identifier,
                "code": issue.code,
                "message": issue.message,
                "detected_at": issue.detected_at,
            }
            for issue in run.issues.all()
        ]
    return payload


def _pipeline_payload(pipeline_key: str, history_limit: int = 0) -> dict:
    metadata = PIPELINES[pipeline_key]
    runs = PipelineRun.objects.filter(pipeline_key=pipeline_key)
    latest = runs.first()
    latest_publication = runs.filter(published_at__isnull=False).first()
    payload = {
        "pipeline_key": pipeline_key,
        **metadata,
        "latest_run": _run_payload(latest) if latest else None,
        "last_published_at": latest_publication.published_at if latest_publication else None,
    }
    if history_limit:
        payload["recent_runs"] = [
            _run_payload(run) for run in runs[:history_limit]
        ]
    return payload


def list_pipelines() -> list[dict]:
    return [_pipeline_payload(key) for key in PIPELINES]


def get_pipeline_detail(pipeline_key: str) -> dict | None:
    if pipeline_key not in PIPELINES:
        return None
    return _pipeline_payload(pipeline_key, history_limit=10)


def get_pipeline_run(pipeline_key: str, run_id: int) -> dict | None:
    if pipeline_key not in PIPELINES:
        return None
    run = PipelineRun.objects.filter(
        pipeline_key=pipeline_key,
        pk=run_id,
    ).prefetch_related("issues").first()
    return _run_payload(run, include_issues=True) if run else None
