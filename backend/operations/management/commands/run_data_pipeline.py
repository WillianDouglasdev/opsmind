from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from operations.ingestion.runner import PipelineExecutionError, run_orders_pipeline


class Command(BaseCommand):
    help = "Executa uma pipeline de dados registrada pelo OpsMind."

    def add_arguments(self, parser) -> None:
        parser.add_argument("pipeline", choices=["orders"], help="Pipeline a executar.")
        parser.add_argument(
            "--source",
            type=Path,
            default=Path(settings.BASE_DIR) / "data" / "source" / "orders.json",
            help="Arquivo JSON de entrada. O padrão é a exportação demonstrativa versionada.",
        )

    def handle(self, *args, **options) -> None:
        try:
            run = run_orders_pipeline(options["source"])
        except PipelineExecutionError as error:
            self._write_summary(error.run)
            raise CommandError(error.run.error_message) from error
        self._write_summary(run)

    def _write_summary(self, run) -> None:
        quality = (
            f"{run.quality_percentage:.2f}%"
            if run.quality_percentage is not None
            else "sem base"
        )
        lines = [
            f"Pipeline: {run.pipeline_key}",
            f"Fonte: {run.source_name}",
            f"Extract: {run.records_received} recebidos",
            f"Validate: {run.records_valid} válidos · {run.records_rejected} rejeitados",
            f"Transform: {run.steps['transform']['records'] or 0} processados",
            f"Load: {run.records_loaded} carregados",
            f"Status: {run.status}",
            f"Qualidade: {quality}",
            f"Duração: {(run.duration_ms or 0) / 1000:.3f}s",
            f"Execução: #{run.pk}",
        ]
        self.stdout.write("\n".join(lines))
