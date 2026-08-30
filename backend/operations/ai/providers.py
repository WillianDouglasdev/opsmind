from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from django.conf import settings
from google import genai
from google.genai import types
from pydantic import ValidationError

from operations.ai.intents import (
    Intent,
    IntentClassification,
    classify_intent_locally,
)
from operations.ai.prompts import (
    CLASSIFICATION_PROMPT,
    SYSTEM_PROMPT,
    build_explanation_prompt,
)

GEMINI_TIMEOUT_MS = 30_000


class AIConfigurationError(Exception):
    pass


class AIProviderError(Exception):
    pass


class AIProvider(Protocol):
    name: str

    def classify_intent(self, question: str) -> IntentClassification: ...

    def explain(self, question: str, intent: Intent, context: dict) -> str: ...


def _pt_number(value, digits: int = 2) -> str:
    return f"{float(value):.{digits}f}".replace(".", ",")


def _currency(value) -> str:
    number = Decimal(str(value))
    formatted = f"{number:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


class MockAIProvider:
    name = "mock"

    def classify_intent(self, question: str) -> IntentClassification:
        return classify_intent_locally(question)

    def explain(self, question: str, intent: Intent, context: dict) -> str:
        # O mock usa somente o contexto recebido e mantém a demo funcional sem custo de API.
        if intent == Intent.DELIVERY_DELAYS:
            branch = context["worst_branch"]
            tickets = context["delivery_tickets"]
            return (
                f"Foram registrados {context['delayed_orders']} pedidos atrasados, com taxa "
                f"de {_pt_number(context['current_rate'])}% contra "
                f"{_pt_number(context['previous_rate'])}% no período anterior. O crescimento "
                f"relativo foi de {_pt_number(context['growth_percentage'])}%. A filial "
                f"{branch['name']} apresentou a maior taxa, com "
                f"{_pt_number(branch['delay_rate'])}%. Também foi observado aumento de "
                f"{_pt_number(tickets['change_percentage'])}% nos chamados de entrega. Esses "
                "sinais aparecem associados, mas não comprovam uma relação causal."
            )
        if intent == Intent.BRANCH_PERFORMANCE:
            return (
                f"A filial {context['branch']['name']} apresenta a maior taxa de atraso: "
                f"{_pt_number(context['branch']['delay_rate'])}%, frente a "
                f"{_pt_number(context['overall_rate'])}% na operação. A diferença é de "
                f"{_pt_number(context['gap_percentage_points'])} pontos percentuais, com "
                f"{context['branch']['delayed_orders']} pedidos atrasados no período recente."
            )
        if intent == Intent.INVENTORY_RISK:
            return (
                f"Existem {context['occurrences']} combinações de filial e produto abaixo "
                f"do estoque mínimo, envolvendo {context['product_count']} produtos e déficit "
                f"total de {context['total_deficit']} unidades. Esses produtos aparecem em "
                f"{context['related_delayed_orders']} pedidos atrasados recentes. A ocorrência "
                "simultânea é um indício operacional e não demonstra que o estoque causou os "
                "atrasos."
            )
        if intent == Intent.CUSTOMER_RISK:
            return (
                f"Foram identificados {context['affected_customers']} clientes estratégicos "
                f"com ocorrências recorrentes. Eles concentram {_currency(context['revenue'])} "
                f"de faturamento no período, {context['delayed_orders']} pedidos atrasados e "
                f"{context['tickets']} chamados."
            )
        if intent == Intent.TICKET_ANALYSIS:
            return (
                f"A operação possui {context['total']} chamados, dos quais "
                f"{context['active']} estão abertos ou em andamento. Os chamados de entrega "
                f"passaram de {context['delivery_previous']} para "
                f"{context['delivery_recent']}, variação de "
                f"{_pt_number(context['delivery_change_percentage'])}%."
            )
        if intent == Intent.EXECUTIVE_SUMMARY:
            health = context["operational_health"]
            return (
                f"A Saúde Operacional está em {health['score']} pontos, classificada como "
                f"{health['status']}. Nos últimos 30 dias foram registrados "
                f"{context['orders']} pedidos, com faturamento de "
                f"{_currency(context['revenue'])}. A taxa de atraso está em "
                f"{_pt_number(context['delay_rate'])}% e há {context['active_tickets']} "
                f"chamados ativos. O principal sinal observado é "
                f"{context['primary_alert'].lower()}."
            )
        return "Não há dados suficientes para responder a esta pergunta."


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        self.model = model
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )

    def classify_intent(self, question: str) -> IntentClassification:
        try:
            # O schema impede que texto livre escolha qual analytics será executado.
            response = self.client.models.generate_content(
                model=self.model,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=CLASSIFICATION_PROMPT,
                    response_mime_type="application/json",
                    response_schema=IntentClassification,
                    temperature=0,
                    max_output_tokens=120,
                ),
            )
        except Exception as error:
            raise AIProviderError("Falha ao classificar a intenção com o provider.") from error

        try:
            if isinstance(response.parsed, IntentClassification):
                return response.parsed
            if response.parsed is not None:
                return IntentClassification.model_validate(response.parsed)
            if response.text:
                return IntentClassification.model_validate_json(response.text)
        except (ValidationError, ValueError, TypeError):
            pass
        # Uma saída vazia ou inválida fica fora do escopo em vez de ser adivinhada.
        return IntentClassification(intent=Intent.UNKNOWN, confidence=0.0)

    def explain(self, question: str, intent: Intent, context: dict) -> str:
        try:
            # O Gemini recebe métricas prontas e não possui acesso ao ORM ou ao banco.
            response = self.client.models.generate_content(
                model=self.model,
                contents=build_explanation_prompt(question, intent, context),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=450,
                ),
            )
        except Exception as error:
            raise AIProviderError("Falha ao gerar a explicação com o provider.") from error
        if not response.text or not response.text.strip():
            raise AIProviderError("O provider retornou uma resposta vazia.")
        return response.text.strip()


def get_ai_provider() -> AIProvider:
    # O mock como padrão permite iniciar o projeto mesmo sem configuração do Gemini.
    if settings.AI_PROVIDER == "mock":
        return MockAIProvider()
    if settings.AI_PROVIDER == "gemini":
        if not settings.GEMINI_API_KEY:
            raise AIConfigurationError(
                "AI_PROVIDER está configurado como gemini, mas GEMINI_API_KEY está ausente."
            )
        if not settings.GEMINI_MODEL:
            raise AIConfigurationError(
                "AI_PROVIDER está configurado como gemini, mas GEMINI_MODEL está ausente."
            )
        return GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
    raise AIConfigurationError(
        "AI_PROVIDER inválido. Utilize 'mock' ou 'gemini'."
    )
