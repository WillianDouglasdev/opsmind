import unicodedata
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# Poucas intents mantêm cada pergunta ligada a uma análise conhecida e testável.
class Intent(str, Enum):
    DELIVERY_DELAYS = "DELIVERY_DELAYS"
    CUSTOMER_RISK = "CUSTOMER_RISK"
    INVENTORY_RISK = "INVENTORY_RISK"
    BRANCH_PERFORMANCE = "BRANCH_PERFORMANCE"
    TICKET_ANALYSIS = "TICKET_ANALYSIS"
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    UNKNOWN = "UNKNOWN"


class IntentClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)


INTENT_KEYWORDS = {
    Intent.TICKET_ANALYSIS: ("chamado", "chamados", "ticket", "tickets", "atendimento"),
    Intent.CUSTOMER_RISK: ("cliente", "clientes", "estrategico", "estrategicos"),
    Intent.BRANCH_PERFORMANCE: ("filial", "filiais", "unidade", "unidades", "contagem"),
    Intent.INVENTORY_RISK: (
        "estoque",
        "produto",
        "produtos",
        "reposicao",
        "faltando",
        "falta",
    ),
    Intent.DELIVERY_DELAYS: ("atraso", "atrasos", "entrega", "entregas", "prazo", "prazos"),
    Intent.EXECUTIVE_SUMMARY: (
        "resumo",
        "resuma",
        "operacao",
        "situacao",
        "panorama",
    ),
}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def classify_intent_locally(question: str) -> IntentClassification:
    # O modo local só precisa de um roteamento previsível, não de um NLP sofisticado.
    normalized_question = _normalize(question)
    scores = {
        intent: sum(keyword in normalized_question for keyword in keywords)
        for intent, keywords in INTENT_KEYWORDS.items()
    }
    best_intent, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        return IntentClassification(intent=Intent.UNKNOWN, confidence=0.0)
    return IntentClassification(
        intent=best_intent,
        confidence=round(min(0.98, 0.72 + best_score * 0.08), 2),
    )
