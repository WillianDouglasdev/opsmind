"""Composição determinística de investigações operacionais derivadas dos dados."""

from urllib.parse import urlencode

from operations.alerts.rules import branch_performance_rule
from operations.analytics.queries import (
    critical_inventory_signals,
    delay_metrics,
    delivery_ticket_metrics,
    percentage_change,
    recent_delayed_order_impact,
    strategic_customer_impact,
)
from operations.operation import build_branch_detail, build_delay_overview


class InvestigationNotFound(Exception):
    pass


def _path(path: str, **params) -> str:
    query = urlencode({key: value for key, value in params.items() if value is not None})
    return f"{path}?{query}" if query else path


def _severity(branch: dict, operation_rate: float) -> str:
    alert = branch_performance_rule(
        {
            "branch_id": branch["id"],
            "branch_name": branch["name"],
            "total_orders": branch["orders"],
            "delayed_orders": branch["delayed_orders"],
            "delay_rate": branch["delay_rate"],
        },
        operation_rate,
    )
    return alert["severity"] if alert else "low"


def _evidence(
    *,
    key: str,
    evidence_type: str,
    title: str,
    description: str,
    current: dict,
    source: str,
    importance: str = "related",
    comparison: dict | None = None,
    difference: dict | None = None,
    change: dict | None = None,
    detail_url: str | None = None,
) -> dict:
    return {
        "key": key,
        "type": evidence_type,
        "title": title,
        "description": description,
        "current": current,
        "comparison": comparison,
        "difference": difference,
        "change": change,
        "importance": importance,
        "source": source,
        "detail_url": detail_url,
    }


def _empty_detail(days: int, period: dict) -> dict:
    return {
        "key": "delivery-delays",
        "type": "delivery_delays",
        "data_status": "empty",
        "period": period,
        "summary": None,
        "evidence": [],
        "timeline": [],
        "next_steps": [],
        "causality_notice": (
            "Não há pedidos atrasados no recorte selecionado. A ausência de sinais "
            "adicionais é um resultado válido."
        ),
        "navigation": {
            "investigations_url": _path("/investigations", days=days),
            "operation_url": _path("/operation/delays", days=days),
        },
    }


def list_investigations(days: int = 30) -> dict:
    overview = build_delay_overview(days)
    delayed_branches = [
        branch for branch in overview["branches"] if branch["delayed_orders"] > 0
    ]
    if not delayed_branches:
        return {"period": overview["period"], "items": []}

    branch = max(
        delayed_branches,
        key=lambda item: (item["delay_rate"], item["delayed_orders"]),
    )
    severity = _severity(branch, overview["metrics"]["delay_rate"])
    return {
        "period": overview["period"],
        "items": [
            {
                "key": "delivery-delays",
                "type": "delivery_delays",
                "title": "Atrasos de entrega",
                "description": (
                    "Reúne fatos operacionais relacionados aos pedidos atrasados, "
                    "sem atribuir causalidade."
                ),
                "severity": severity,
                "branch": {
                    key: branch[key] for key in ("id", "name", "city", "state")
                },
                "delay_rate": branch["delay_rate"],
                "delayed_orders": branch["delayed_orders"],
                "detail_url": _path(
                    "/investigations/delivery-delays",
                    days=days,
                    branch=branch["id"],
                ),
            }
        ],
    }


def build_delivery_delay_investigation(
    *,
    days: int = 30,
    branch_id: int | None = None,
) -> dict:
    overview = build_delay_overview(days)
    delayed_branches = [
        branch for branch in overview["branches"] if branch["delayed_orders"] > 0
    ]
    if not delayed_branches:
        return _empty_detail(days, overview["period"])

    selected = (
        next((branch for branch in overview["branches"] if branch["id"] == branch_id), None)
        if branch_id is not None
        else max(
            delayed_branches,
            key=lambda item: (item["delay_rate"], item["delayed_orders"]),
        )
    )
    if selected is None:
        raise InvestigationNotFound("Filial não encontrada.")
    if selected["delayed_orders"] == 0:
        return _empty_detail(days, overview["period"])

    branch_id = selected["id"]
    branch_detail = build_branch_detail(branch_id, days)
    branch_delays = delay_metrics(days=days, branch_id=branch_id)
    tickets = delivery_ticket_metrics(days=days, branch_id=branch_id)
    inventory = [
        item
        for item in critical_inventory_signals(days=days, branch_id=branch_id)
        if item["delayed_orders"] > 0
    ]
    strategic = strategic_customer_impact(days=days, branch_id=branch_id)
    impact = recent_delayed_order_impact(days=days, branch_id=branch_id)
    operation_rate = overview["metrics"]["delay_rate"]
    gap = round(selected["delay_rate"] - operation_rate, 2)
    growth = percentage_change(
        selected["delay_rate"],
        selected["previous_delay_rate"],
    )
    order_url = _path(
        f"/operation/branches/{branch_id}",
        days=days,
        delivery="late",
    )

    evidence = [
        _evidence(
            key="delay-rate",
            evidence_type="delivery",
            title="Taxa de atraso da filial",
            description=(
                "A taxa atual é comparada ao período anterior com a mesma duração."
            ),
            current={"label": "Período atual", "value": selected["delay_rate"], "unit": "percentage"},
            comparison={"label": "Período anterior", "value": selected["previous_delay_rate"], "unit": "percentage"},
            difference={"label": "Diferença", "value": round(selected["delay_rate"] - selected["previous_delay_rate"], 2), "unit": "percentage_points"},
            change={"label": "Variação", "value": growth, "unit": "percentage_change"},
            importance="primary",
            source="Pedidos · status = delayed",
            detail_url=order_url,
        ),
        _evidence(
            key="affected-orders",
            evidence_type="delivery",
            title="Pedidos e valor afetados",
            description="Pedidos classificados como atrasados no recorte selecionado.",
            current={"label": "Pedidos atrasados", "value": impact["delayed_orders"], "unit": "count"},
            comparison={"label": "Valor relacionado", "value": impact["affected_revenue"], "unit": "currency"},
            importance="primary",
            source="Pedidos · filial e período selecionados",
            detail_url=order_url,
        ),
    ]

    if tickets["value"] or tickets["previous_value"]:
        evidence.append(
            _evidence(
                key="delivery-tickets",
                evidence_type="tickets",
                title="Chamados relacionados à entrega",
                description=(
                    "Os chamados ocorreram no mesmo recorte. Essa coincidência temporal "
                    "não comprova que tenham causado os atrasos."
                ),
                current={"label": "Período atual", "value": tickets["value"], "unit": "count"},
                comparison={"label": "Período anterior", "value": tickets["previous_value"], "unit": "count"},
                difference={"label": "Diferença", "value": tickets["value"] - tickets["previous_value"], "unit": "count"},
                change={"label": "Variação", "value": tickets["change_percentage"], "unit": "percentage_change"},
                source="Chamados · categoria entrega vinculados à filial",
            )
        )

    for item in inventory[:5]:
        evidence.append(
            _evidence(
                key=f"inventory-{item['product_id']}",
                evidence_type="inventory",
                title=f"{item['product__sku']} · {item['product__name']}",
                description=(
                    "O produto aparece simultaneamente em pedidos atrasados e em situação "
                    "de estoque crítico. É um sinal relacionado, não uma causa confirmada."
                ),
                current={"label": "Pedidos atrasados", "value": item["delayed_orders"], "unit": "count"},
                comparison={"label": "Déficit de estoque", "value": item["deficit"], "unit": "count"},
                source="Estoque atual + itens dos pedidos atrasados",
                detail_url=order_url,
            )
        )

    if strategic["affected_customers"]:
        evidence.append(
            _evidence(
                key="strategic-customers",
                evidence_type="customers",
                title="Clientes estratégicos afetados",
                description=(
                    "Clientes estratégicos com ocorrências recorrentes no mesmo período e filial."
                ),
                current={"label": "Clientes", "value": strategic["affected_customers"], "unit": "count"},
                comparison={"label": "Pedidos atrasados", "value": strategic["delayed_orders"], "unit": "count"},
                source="Clientes estratégicos + pedidos e chamados relacionados",
                detail_url=order_url,
            )
        )

    timeline = [
        {
            "date": point["date"],
            "type": "delayed_orders",
            "title": "Pedidos atrasados registrados",
            "description": (
                f"{point['delayed_orders']} de {point['orders']} pedidos do dia "
                "foram classificados como atrasados."
            ),
            "value": point["delayed_orders"],
            "unit": "count",
            "source": "Pedidos · status = delayed",
            "detail_url": order_url,
        }
        for point in branch_detail["trend"]
        if point["delayed_orders"] > 0
    ][-8:]

    next_steps = [
        {
            "key": "review-delayed-orders",
            "title": "Revisar os pedidos atrasados mais antigos",
            "description": "Abra o recorte da filial e priorize a revisão dos pedidos pendentes.",
            "detail_url": order_url,
        }
    ]
    if tickets["value"] > tickets["previous_value"]:
        next_steps.append(
            {
                "key": "review-delivery-tickets",
                "title": "Verificar os chamados de entrega recentes",
                "description": "Compare assuntos recorrentes sem tratá-los como causa confirmada.",
                "detail_url": None,
            }
        )
    if inventory:
        next_steps.append(
            {
                "key": "review-related-inventory",
                "title": "Revisar a disponibilidade dos produtos relacionados",
                "description": "Confira os itens abaixo do mínimo que também aparecem nos atrasos.",
                "detail_url": order_url,
            }
        )
    if strategic["affected_customers"]:
        next_steps.append(
            {
                "key": "prioritize-strategic-customers",
                "title": "Priorizar pedidos de clientes estratégicos",
                "description": "Revise primeiro os clientes com ocorrências recorrentes no recorte.",
                "detail_url": order_url,
            }
        )
    next_steps.append(
        {
            "key": "compare-branches",
            "title": "Comparar com outras filiais",
            "description": "Use a visão de atrasos para verificar se o sinal está concentrado.",
            "detail_url": _path("/operation/delays", days=days),
        }
    )

    return {
        "key": "delivery-delays",
        "type": "delivery_delays",
        "data_status": "complete" if len(evidence) > 2 else "partial",
        "period": overview["period"],
        "summary": {
            "title": f"Aumento de atrasos em {selected['name']}",
            "situation": (
                "A taxa de atrasos da filial está acima da média operacional."
                if gap > 0
                else "A filial possui pedidos atrasados no período selecionado."
            ),
            "severity": _severity(selected, operation_rate),
            "branch": {key: selected[key] for key in ("id", "name", "city", "state")},
            "branch_delay_rate": selected["delay_rate"],
            "operation_delay_rate": operation_rate,
            "difference_percentage_points": gap,
            "previous_delay_rate": selected["previous_delay_rate"],
            "change_percentage": growth,
            "delayed_orders": selected["delayed_orders"],
            "impacted_customers": impact["impacted_customers"],
            "affected_revenue": impact["affected_revenue"],
        },
        "evidence": evidence,
        "timeline": timeline,
        "next_steps": next_steps,
        "causality_notice": (
            "As evidências mostram ocorrências simultâneas e comparações operacionais. "
            "Elas orientam a investigação, mas não confirmam relações de causa e efeito."
        ),
        "navigation": {
            "investigations_url": _path("/investigations", days=days),
            "operation_url": order_url,
        },
    }
