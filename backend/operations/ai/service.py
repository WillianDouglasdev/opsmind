import logging

from operations.ai.intents import Intent, IntentClassification, classify_intent_locally
from operations.ai.providers import AIProvider, MockAIProvider, get_ai_provider
from operations.alerts.engine import get_active_alerts
from operations.analytics.dashboard import build_dashboard_summary
from operations.analytics.queries import (
    branch_delay_rates,
    branch_delivery_ticket_count,
    critical_inventory_related_order_count,
    critical_inventory_signals,
    delay_metrics,
    delayed_product_metrics,
    delivery_ticket_metrics,
    recent_delayed_order_impact,
    strategic_customer_impact,
    ticket_analysis_metrics,
)

logger = logging.getLogger(__name__)

UNKNOWN_ANSWER = (
    "Atualmente consigo analisar entregas, filiais, estoque, clientes estratégicos, "
    "chamados e o resumo da operação."
)


def _metric(label: str, value, unit: str) -> dict:
    return {"label": label, "value": value, "unit": unit}


def _delivery_context() -> tuple[dict, list[dict]]:
    delays = delay_metrics()
    impact = recent_delayed_order_impact()
    worst_branch = max(branch_delay_rates(), key=lambda branch: branch["delay_rate"])
    tickets = delivery_ticket_metrics()
    strategic = strategic_customer_impact()
    products = critical_inventory_signals()[:5]
    context = {
        "delayed_orders": impact["delayed_orders"],
        "current_rate": delays["rate"],
        "previous_rate": delays["previous_rate"],
        "growth_percentage": delays["change_percentage"],
        "impacted_customers": impact["impacted_customers"],
        "affected_revenue": impact["affected_revenue"],
        "worst_branch": {
            "name": worst_branch["branch_name"],
            "delay_rate": worst_branch["delay_rate"],
            "delayed_orders": worst_branch["delayed_orders"],
        },
        "related_products": [
            {
                "sku": item["product__sku"],
                "branch": item["branch__name"],
                "delayed_orders": item["delayed_orders"],
            }
            for item in products
        ],
        "delivery_tickets": tickets,
        "strategic_customers": {
            "affected": strategic["affected_customers"],
            "delayed_orders": strategic["delayed_orders"],
            "tickets": strategic["tickets"],
        },
    }
    evidence = [
        _metric("Pedidos atrasados", impact["delayed_orders"], "count"),
        _metric("Taxa de atraso", delays["rate"], "percentage"),
        _metric("Variação da taxa", delays["change_percentage"], "percentage_change"),
        _metric("Filial com maior taxa", worst_branch["branch_name"], "text"),
    ]
    return context, evidence


def _branch_context() -> tuple[dict, list[dict]]:
    delays = delay_metrics()
    worst_branch = max(branch_delay_rates(), key=lambda branch: branch["delay_rate"])
    gap = round(worst_branch["delay_rate"] - delays["rate"], 2)
    products = delayed_product_metrics(branch_id=worst_branch["branch_id"])[:5]
    context = {
        "branch": {
            "name": worst_branch["branch_name"],
            "total_orders": worst_branch["total_orders"],
            "delayed_orders": worst_branch["delayed_orders"],
            "delay_rate": worst_branch["delay_rate"],
        },
        "overall_rate": delays["rate"],
        "gap_percentage_points": gap,
        "delivery_tickets": branch_delivery_ticket_count(worst_branch["branch_id"]),
        "related_products": products,
    }
    evidence = [
        _metric("Filial", worst_branch["branch_name"], "text"),
        _metric("Taxa da filial", worst_branch["delay_rate"], "percentage"),
        _metric("Média geral", delays["rate"], "percentage"),
        _metric("Diferença", gap, "percentage_points"),
    ]
    return context, evidence


def _inventory_context() -> tuple[dict, list[dict]]:
    items = critical_inventory_signals()
    context = {
        "occurrences": len(items),
        "product_count": len({item["product_id"] for item in items}),
        "total_deficit": sum(item["deficit"] for item in items),
        "related_delayed_orders": critical_inventory_related_order_count(),
        "items": [
            {
                "sku": item["product__sku"],
                "product": item["product__name"],
                "branch": item["branch__name"],
                "current_quantity": item["current_quantity"],
                "minimum_quantity": item["minimum_quantity"],
                "deficit": item["deficit"],
                "delayed_orders": item["delayed_orders"],
            }
            for item in items
        ],
    }
    evidence = [
        _metric("Ocorrências críticas", context["occurrences"], "count"),
        _metric("Produtos afetados", context["product_count"], "count"),
        _metric("Déficit total", context["total_deficit"], "count"),
        _metric(
            "Pedidos atrasados relacionados",
            context["related_delayed_orders"],
            "count",
        ),
    ]
    return context, evidence


def _customer_context() -> tuple[dict, list[dict]]:
    impact = strategic_customer_impact()
    context = {
        "affected_customers": impact["affected_customers"],
        "revenue": impact["revenue"],
        "delayed_orders": impact["delayed_orders"],
        "tickets": impact["tickets"],
        "top_customers": impact["customers"][:5],
    }
    evidence = [
        _metric("Clientes estratégicos afetados", impact["affected_customers"], "count"),
        _metric("Faturamento no período", impact["revenue"], "currency"),
        _metric("Pedidos atrasados", impact["delayed_orders"], "count"),
        _metric("Chamados", impact["tickets"], "count"),
    ]
    return context, evidence


def _ticket_context() -> tuple[dict, list[dict]]:
    context = ticket_analysis_metrics()
    evidence = [
        _metric("Chamados totais", context["total"], "count"),
        _metric("Chamados ativos", context["active"], "count"),
        _metric("Chamados de entrega recentes", context["delivery_recent"], "count"),
        _metric(
            "Variação dos chamados de entrega",
            context["delivery_change_percentage"],
            "percentage_change",
        ),
    ]
    return context, evidence


def _executive_context() -> tuple[dict, list[dict]]:
    summary = build_dashboard_summary()
    alerts = get_active_alerts()
    context = {
        "operational_health": summary["operational_health"],
        "revenue": summary["revenue"]["value"],
        "revenue_change_percentage": summary["revenue"]["change_percentage"],
        "orders": summary["orders"]["value"],
        "orders_change_percentage": summary["orders"]["change_percentage"],
        "delayed_orders": summary["delayed_orders"]["value"],
        "delay_rate": summary["delayed_orders"]["rate"],
        "delay_change_percentage": summary["delayed_orders"]["change_percentage"],
        "active_tickets": summary["open_tickets"]["value"],
        "alerts": [
            {"severity": alert["severity"], "title": alert["title"]}
            for alert in alerts
        ],
        "primary_alert": alerts[0]["title"] if alerts else "Nenhum alerta ativo",
    }
    evidence = [
        _metric("Saúde Operacional", summary["operational_health"]["score"], "score"),
        _metric("Faturamento", summary["revenue"]["value"], "currency"),
        _metric("Pedidos", summary["orders"]["value"], "count"),
        _metric("Taxa de atraso", summary["delayed_orders"]["rate"], "percentage"),
        _metric("Chamados ativos", summary["open_tickets"]["value"], "count"),
        _metric("Alertas ativos", len(alerts), "count"),
    ]
    return context, evidence


# Cada intent escolhe um contexto explícito; o modelo nunca decide qual query executar.
CONTEXT_BUILDERS = {
    Intent.DELIVERY_DELAYS: _delivery_context,
    Intent.BRANCH_PERFORMANCE: _branch_context,
    Intent.INVENTORY_RISK: _inventory_context,
    Intent.CUSTOMER_RISK: _customer_context,
    Intent.TICKET_ANALYSIS: _ticket_context,
    Intent.EXECUTIVE_SUMMARY: _executive_context,
}


def _fallback_provider(question: str) -> tuple[MockAIProvider, IntentClassification]:
    return MockAIProvider(), classify_intent_locally(question)


def query_assistant(question: str, provider: AIProvider | None = None) -> dict:
    active_provider = provider or get_ai_provider()
    provider_name = active_provider.name
    try:
        classification = active_provider.classify_intent(question)
    except Exception:
        # O fallback local preserva a consulta e o provider retornado deixa isso explícito.
        logger.warning("Falha na classificação do provider; ativando fallback local.")
        active_provider, classification = _fallback_provider(question)
        provider_name = "fallback"

    # UNKNOWN encerra o fluxo antes de consultar analytics ou usar o modelo como chatbot geral.
    if classification.intent == Intent.UNKNOWN:
        return {
            "intent": Intent.UNKNOWN.value,
            "confidence": classification.confidence,
            "answer": UNKNOWN_ANSWER,
            "evidence": [],
            "provider": provider_name,
        }

    context, evidence = CONTEXT_BUILDERS[classification.intent]()
    try:
        answer = active_provider.explain(question, classification.intent, context)
    except Exception:
        # Se só a explicação falhar, reaproveitamos o mesmo contexto no texto determinístico.
        logger.warning("Falha na explicação do provider; ativando fallback local.")
        answer = MockAIProvider().explain(question, classification.intent, context)
        provider_name = "fallback"

    # As evidências são anexadas pelo backend e nunca escolhidas pelo modelo.
    return {
        "intent": classification.intent.value,
        "confidence": classification.confidence,
        "answer": answer,
        "evidence": evidence,
        "provider": provider_name,
    }


def executive_summary(provider: AIProvider | None = None) -> dict:
    active_provider = provider or get_ai_provider()
    provider_name = active_provider.name
    context, evidence = _executive_context()
    question = "Resuma a operação."
    try:
        answer = active_provider.explain(question, Intent.EXECUTIVE_SUMMARY, context)
    except Exception:
        logger.warning("Falha no resumo do provider; ativando fallback local.")
        answer = MockAIProvider().explain(question, Intent.EXECUTIVE_SUMMARY, context)
        provider_name = "fallback"
    return {
        "intent": Intent.EXECUTIVE_SUMMARY.value,
        "confidence": 1.0,
        "answer": answer,
        "evidence": evidence,
        "provider": provider_name,
    }
