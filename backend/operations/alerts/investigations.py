"""Amplia alertas ativos com evidências determinísticas e contexto de recomendações.

_recommendation_context é um contrato interno consumido por actions/recommendations;
o serializer o omite da API. Preserve seus campos ao editar os textos da investigação.
"""

from operations.alerts.engine import get_alert
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
)


class AlertNotFound(Exception):
    pass


def _metric(label: str, value, unit: str) -> dict:
    return {"label": label, "value": value, "unit": unit}


def _section(title: str, description: str, metrics: list[dict]) -> dict:
    return {"title": title, "description": description, "metrics": metrics}


def _delivery_delay_investigation(alert: dict) -> dict:
    # A investigação amplia o alerta com impacto e sinais relacionados, sem recalcular sua regra.
    delays = delay_metrics()
    impact = recent_delayed_order_impact()
    tickets = delivery_ticket_metrics()
    branches = branch_delay_rates()
    worst_branch = max(branches, key=lambda branch: branch["delay_rate"])
    critical_items = critical_inventory_signals()
    strategic = strategic_customer_impact()

    product_evidence = []
    for item in critical_items:
        product_evidence.append(
            _section(
                f"{item['product__sku']} — {item['product__name']}",
                (
                    "O produto está abaixo do estoque mínimo e também aparece em pedidos "
                    "atrasados recentes da filial."
                ),
                [
                    _metric("Filial", item["branch__name"], "text"),
                    _metric("Pedidos atrasados relacionados", item["delayed_orders"], "count"),
                    _metric("Déficit de estoque", item["deficit"], "count"),
                ],
            )
        )

    return {
        "alert": alert,
        "_recommendation_context": {
            "impact": impact,
            "tickets": tickets,
            "worst_branch": worst_branch,
        },
        "context": (
            "Os sinais abaixo estão associados ao aumento dos atrasos. Eles orientam a "
            "investigação, mas não comprovam causalidade."
        ),
        "impact": [
            _metric("Pedidos atrasados", impact["delayed_orders"], "count"),
            _metric("Clientes impactados", impact["impacted_customers"], "count"),
            _metric("Valor dos pedidos afetados", impact["affected_revenue"], "currency"),
            _metric("Taxa atual", delays["rate"], "percentage"),
            _metric("Taxa anterior", delays["previous_rate"], "percentage"),
        ],
        "related_signals": [
            _section(
                f"Filial {worst_branch['branch_name']}",
                "Maior taxa de atraso entre as filiais no período recente.",
                [
                    _metric("Taxa de atraso", worst_branch["delay_rate"], "percentage"),
                    _metric("Pedidos atrasados", worst_branch["delayed_orders"], "count"),
                ],
            ),
            _section(
                "Chamados de entrega",
                "O volume de chamados de entrega também aumentou no período.",
                [
                    _metric("Chamados recentes", tickets["value"], "count"),
                    _metric("Período anterior", tickets["previous_value"], "count"),
                    _metric(
                        "Variação",
                        tickets["change_percentage"],
                        "percentage_change",
                    ),
                ],
            ),
            _section(
                "Clientes estratégicos afetados",
                "Clientes estratégicos com atrasos ou chamados recorrentes.",
                [
                    _metric("Clientes", strategic["affected_customers"], "count"),
                    _metric("Atrasos", strategic["delayed_orders"], "count"),
                    _metric("Chamados", strategic["tickets"], "count"),
                ],
            ),
        ],
        "evidence": product_evidence,
    }


def _branch_performance_investigation(alert: dict) -> dict:
    branch_id = alert["context"]["branch_id"]
    delays = delay_metrics()
    branch = next(
        branch for branch in branch_delay_rates() if branch["branch_id"] == branch_id
    )
    gap = round(branch["delay_rate"] - delays["rate"], 2)
    ticket_count = branch_delivery_ticket_count(branch_id)
    products = delayed_product_metrics(branch_id=branch_id)[:5]

    evidence = [
        _section(
            f"{product['sku']} — {product['name']}",
            "Produto presente em pedidos atrasados recentes da filial.",
            [
                _metric("Pedidos atrasados", product["delayed_orders"], "count"),
                _metric("Unidades relacionadas", product["delayed_units"], "count"),
            ],
        )
        for product in products
    ]

    return {
        "alert": alert,
        "_recommendation_context": {
            "branch": branch,
            "gap": gap,
            "products": products,
        },
        "context": (
            "A comparação utiliza a taxa recente da filial contra a taxa geral da "
            "operação, exigindo volume mínimo de pedidos."
        ),
        "impact": [
            _metric("Filial", branch["branch_name"], "text"),
            _metric("Pedidos recentes", branch["total_orders"], "count"),
            _metric("Pedidos atrasados", branch["delayed_orders"], "count"),
            _metric("Taxa de atraso", branch["delay_rate"], "percentage"),
            _metric("Média geral", delays["rate"], "percentage"),
            _metric("Diferença", gap, "percentage_points"),
        ],
        "related_signals": [
            _section(
                "Chamados de entrega relacionados",
                "Chamados recentes vinculados a pedidos da filial.",
                [_metric("Chamados", ticket_count, "count")],
            )
        ],
        "evidence": evidence,
    }


def _inventory_risk_investigation(alert: dict) -> dict:
    # Estoque e atraso aparecem juntos, mas o texto preserva a diferença entre relação e causa.
    items = critical_inventory_signals()
    distinct_products = len({item["product_id"] for item in items})
    total_deficit = sum(item["deficit"] for item in items)
    related_orders = critical_inventory_related_order_count()

    evidence = [
        _section(
            f"{item['product__sku']} — {item['product__name']}",
            (
                f"Estoque abaixo do mínimo na filial {item['branch__name']}. Esse produto "
                f"também aparece em {item['delayed_orders']} pedidos atrasados recentes."
            ),
            [
                _metric("Quantidade atual", item["current_quantity"], "count"),
                _metric("Quantidade mínima", item["minimum_quantity"], "count"),
                _metric("Déficit", item["deficit"], "count"),
                _metric(
                    "Abaixo do mínimo",
                    item["percentage_below_minimum"],
                    "percentage",
                ),
                _metric("Pedidos atrasados relacionados", item["delayed_orders"], "count"),
            ],
        )
        for item in items
    ]

    return {
        "alert": alert,
        "_recommendation_context": {
            "items": items,
            "total_deficit": total_deficit,
            "related_orders": related_orders,
        },
        "context": (
            "O estoque é um snapshot atual. A presença dos produtos em pedidos atrasados "
            "é um sinal relacionado e não comprova que o estoque causou os atrasos."
        ),
        "impact": [
            _metric("Ocorrências críticas", len(items), "count"),
            _metric("Produtos afetados", distinct_products, "count"),
            _metric("Déficit total", total_deficit, "count"),
            _metric(
                "Pedidos atrasados relacionados",
                related_orders,
                "count",
            ),
        ],
        "related_signals": [],
        "evidence": evidence,
    }


def _strategic_customer_investigation(alert: dict) -> dict:
    impact = strategic_customer_impact()
    evidence = [
        _section(
            customer["name"],
            "Cliente estratégico com ocorrências recorrentes no período recente.",
            [
                _metric("Pedidos atrasados", customer["recent_delays"], "count"),
                _metric("Chamados", customer["recent_tickets"], "count"),
            ],
        )
        for customer in impact["customers"]
    ]

    return {
        "alert": alert,
        "_recommendation_context": impact,
        "context": (
            "A investigação reúne clientes estratégicos com dois ou mais atrasos ou "
            "dois ou mais chamados recentes."
        ),
        "impact": [
            _metric("Clientes afetados", impact["affected_customers"], "count"),
            _metric("Faturamento no período", impact["revenue"], "currency"),
            _metric("Pedidos atrasados", impact["delayed_orders"], "count"),
            _metric("Chamados", impact["tickets"], "count"),
        ],
        "related_signals": [],
        "evidence": evidence,
    }


INVESTIGATION_BUILDERS = {
    "DELIVERY_DELAY_INCREASE": _delivery_delay_investigation,
    "BRANCH_PERFORMANCE": _branch_performance_investigation,
    "INVENTORY_RISK": _inventory_risk_investigation,
    "STRATEGIC_CUSTOMER_RISK": _strategic_customer_investigation,
}


def build_investigation(alert_key: str) -> dict:
    # Só investigamos alertas que continuam ativos no estado atual dos dados.
    alert = get_alert(alert_key)
    if alert is None:
        raise AlertNotFound(alert_key)
    return INVESTIGATION_BUILDERS[alert["type"]](alert)
