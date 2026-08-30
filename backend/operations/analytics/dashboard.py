from decimal import Decimal

from operations.analytics.queries import (
    active_ticket_metrics,
    branch_delay_rates,
    critical_inventory_items,
    delay_metrics,
    delivery_ticket_metrics,
    monthly_on_time_delivery,
    order_metrics,
    recurring_strategic_customers,
    revenue_metrics,
)
from operations.demo import DEMO_REFERENCE_DATE
from operations.models import Customer, Inventory


def _bounded_penalty(value: float, maximum: int) -> int:
    return min(maximum, max(0, round(value)))


def calculate_operational_health(metrics: dict) -> dict:
    # O score é determinístico: a IA explica o resultado, mas nunca decide a saúde da operação.
    components = [
        {
            "name": "Atrasos recentes",
            "impact": -_bounded_penalty(metrics["delay_rate"] * 0.7, 20),
            "value": metrics["delay_rate"],
            "unit": "percent",
        },
        {
            "name": "Crescimento dos atrasos",
            "impact": -_bounded_penalty(max(0, metrics["delay_growth"]) * 0.15, 10),
            "value": metrics["delay_growth"],
            "unit": "percent",
        },
        {
            "name": "Estoque crítico",
            "impact": -_bounded_penalty(metrics["critical_inventory_rate"] * 1.5, 10),
            "value": metrics["critical_inventory_rate"],
            "unit": "percent",
        },
        {
            "name": "Chamados ativos",
            "impact": -_bounded_penalty(metrics["active_ticket_rate"] * 0.12, 10),
            "value": metrics["active_ticket_rate"],
            "unit": "percent",
        },
        {
            "name": "Clientes estratégicos afetados",
            "impact": -_bounded_penalty(metrics["strategic_customer_rate"] * 0.08, 8),
            "value": metrics["strategic_customer_rate"],
            "unit": "percent",
        },
        {
            "name": "Desvio da pior filial",
            "impact": -_bounded_penalty(metrics["worst_branch_gap"] * 0.5, 8),
            "value": metrics["worst_branch_gap"],
            "unit": "percentage_points",
        },
    ]

    # Cada sinal tem limite próprio e o resultado final também permanece entre 0 e 100.
    score = max(0, min(100, 100 + sum(component["impact"] for component in components)))
    if score >= 90:
        status = "Saudável"
        description = "Os principais indicadores permanecem em níveis saudáveis."
    elif score >= 75:
        status = "Atenção"
        description = "Alguns indicadores operacionais exigem acompanhamento."
    elif score >= 60:
        status = "Risco moderado"
        description = "Atrasos e sinais operacionais exigem atenção."
    else:
        status = "Risco alto"
        description = "Múltiplos indicadores operacionais estão em condição crítica."

    return {
        "score": score,
        "status": status,
        "description": description,
        "components": components,
    }


def build_dashboard_summary() -> dict:
    revenue = revenue_metrics()
    orders = order_metrics()
    delays = delay_metrics()
    tickets = active_ticket_metrics()
    critical_inventory = critical_inventory_items()
    recurring_customers = recurring_strategic_customers()
    branches = branch_delay_rates()

    # Usamos proporções para comparar sinais de tamanhos diferentes no mesmo score.
    inventory_total = Inventory.objects.count()
    strategic_total = Customer.objects.filter(segment=Customer.Segment.STRATEGIC).count()
    worst_branch_rate = max((branch["delay_rate"] for branch in branches), default=0.0)
    health = calculate_operational_health(
        {
            "delay_rate": delays["rate"],
            "delay_growth": delays["change_percentage"] or 0.0,
            "critical_inventory_rate": (
                round(len(critical_inventory) / inventory_total * 100, 2)
                if inventory_total
                else 0.0
            ),
            "active_ticket_rate": tickets["active_rate"],
            "strategic_customer_rate": (
                round(len(recurring_customers) / strategic_total * 100, 2)
                if strategic_total
                else 0.0
            ),
            "worst_branch_gap": round(max(0.0, worst_branch_rate - delays["rate"]), 2),
        }
    )

    return {
        "reference_date": DEMO_REFERENCE_DATE,
        "operational_health": health,
        "revenue": {
            "value": revenue["value"],
            "change_percentage": revenue["change_percentage"],
        },
        "orders": {
            "value": orders["value"],
            "change_percentage": orders["change_percentage"],
        },
        "delayed_orders": {
            "value": delays["value"],
            "rate": delays["rate"],
            "change_percentage": delays["change_percentage"],
        },
        "open_tickets": tickets,
    }


def build_dashboard_trends() -> dict:
    return {
        "reference_date": DEMO_REFERENCE_DATE,
        "metric": "on_time_delivery_rate",
        "target": 90.0,
        "series": monthly_on_time_delivery(),
    }


def _change_direction(value: float | None) -> str:
    if value is None or value == 0:
        return "neutral"
    return "up" if value > 0 else "down"


def _pt_number(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def build_dashboard_changes() -> dict:
    delays = delay_metrics()
    delivery_tickets = delivery_ticket_metrics()
    revenue = revenue_metrics()
    critical_inventory = critical_inventory_items()

    delay_change = delays["change_percentage"]
    ticket_change = delivery_tickets["change_percentage"]
    revenue_change = revenue["change_percentage"]

    return {
        "reference_date": DEMO_REFERENCE_DATE,
        "items": [
            {
                "type": "percentage",
                "label": "Atrasos nas entregas",
                "value": delay_change,
                "direction": _change_direction(delay_change),
                "tone": "negative" if delay_change and delay_change > 0 else "positive",
                "description": (
                    f"A taxa passou de {_pt_number(delays['previous_rate'])}% para "
                    f"{_pt_number(delays['rate'])}%."
                ),
            },
            {
                "type": "percentage",
                "label": "Chamados de entrega",
                "value": ticket_change,
                "direction": _change_direction(ticket_change),
                "tone": "negative" if ticket_change and ticket_change > 0 else "positive",
                "description": (
                    f"{delivery_tickets['value']} chamados recentes contra "
                    f"{delivery_tickets['previous_value']} no período anterior."
                ),
            },
            {
                "type": "inventory",
                "label": "Estoque crítico",
                "value": float(len(critical_inventory)),
                "direction": "current",
                "tone": "warning",
                "description": (
                    f"{len(critical_inventory)} combinações de filial e produto estão "
                    "abaixo do mínimo."
                ),
            },
            {
                "type": "percentage",
                "label": "Faturamento",
                "value": revenue_change,
                "direction": _change_direction(revenue_change),
                "tone": "positive" if revenue_change and revenue_change > 0 else "negative",
                "description": "Comparação do faturamento operacional entre os períodos.",
            },
        ],
    }
