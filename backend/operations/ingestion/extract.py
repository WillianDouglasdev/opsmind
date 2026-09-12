import json
from pathlib import Path


class ExtractionError(Exception):
    pass


def extract_orders(source_path: Path) -> list[dict]:
    """Lê o RAW sem aplicar regra de negócio ou consultar o banco."""
    try:
        with source_path.open(encoding="utf-8") as source:
            payload = json.load(source)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ExtractionError("Não foi possível ler a fonte JSON de pedidos.") from error

    if not isinstance(payload, list):
        raise ExtractionError("A fonte de pedidos deve conter uma lista JSON.")
    if not all(isinstance(record, dict) for record in payload):
        raise ExtractionError("Cada registro da fonte de pedidos deve ser um objeto JSON.")
    return payload
