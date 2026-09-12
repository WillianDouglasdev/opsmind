from django.utils.text import slugify

from operations.demo import DEMO_REFERENCE_DATE

DELIVERY_DELAY_MIN_RATE = 10.0
# Exigimos crescimento de 15% para não alertar por uma oscilação pequena entre períodos.
DELIVERY_DELAY_GROWTH_THRESHOLD = 15.0
DELIVERY_DELAY_HIGH_GROWTH = 20.0
DELIVERY_DELAY_CRITICAL_RATE = 20.0
DELIVERY_DELAY_CRITICAL_GROWTH = 40.0

# O volume mínimo reduz alertas causados por oscilações em filiais com poucos pedidos.
BRANCH_MIN_ORDERS = 50
# A diferença de 5 p.p. separa um desvio relevante de uma filial apenas ligeiramente pior.
BRANCH_DELAY_GAP_THRESHOLD = 5.0
BRANCH_DELAY_HIGH_GAP = 7.0
BRANCH_DELAY_CRITICAL_GAP = 12.0

INVENTORY_HIGH_OCCURRENCES = 4
INVENTORY_CRITICAL_OCCURRENCES = 8
# Muitos atrasos relacionados elevam a severidade, mas continuam tratados como associação.
INVENTORY_HIGH_RELATED_DELAYS = 20
STRATEGIC_HIGH_CUSTOMERS = 5
STRATEGIC_CRITICAL_CUSTOMERS = 10

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _pt_number(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def delivery_delay_rule(metrics: dict) -> dict | None:
    growth = metrics["change_percentage"]
    # A severidade combina nível atual e crescimento para não olhar apenas um dos sinais.
    if (
        metrics["rate"] < DELIVERY_DELAY_MIN_RATE
        or growth is None
        or growth < DELIVERY_DELAY_GROWTH_THRESHOLD
    ):
        return None

    if (
        metrics["rate"] >= DELIVERY_DELAY_CRITICAL_RATE
        and growth >= DELIVERY_DELAY_CRITICAL_GROWTH
    ):
        severity = "critical"
    elif growth >= DELIVERY_DELAY_HIGH_GROWTH:
        severity = "high"
    else:
        severity = "medium"

    return {
        "key": "delivery-delay-increase",
        "type": "DELIVERY_DELAY_INCREASE",
        "severity": severity,
        "title": "Atrasos nas entregas aumentaram",
        "summary": (
            f"A taxa de atraso aumentou {_pt_number(growth)}% em relação ao período "
            "anterior."
        ),
        "reference_date": DEMO_REFERENCE_DATE,
        "metrics": [
            {"label": "Taxa atual", "value": metrics["rate"], "unit": "percentage"},
            {
                "label": "Taxa anterior",
                "value": metrics["previous_rate"],
                "unit": "percentage",
            },
            {
                "label": "Variação relativa",
                "value": growth,
                "unit": "percentage_change",
            },
        ],
    }


def branch_performance_rule(branch: dict, overall_rate: float) -> dict | None:
    # A chave pública depende do nome da filial e também é guardada nas ActionItems.
    # Renomear uma filial pode mudar essa identidade; a V2 precisará tratar a transição.
    gap = round(branch["delay_rate"] - overall_rate, 2)
    if branch["total_orders"] < BRANCH_MIN_ORDERS or gap < BRANCH_DELAY_GAP_THRESHOLD:
        return None

    if gap >= BRANCH_DELAY_CRITICAL_GAP:
        severity = "critical"
    elif gap >= BRANCH_DELAY_HIGH_GAP:
        severity = "high"
    else:
        severity = "medium"

    return {
        "key": f"branch-performance-{slugify(branch['branch_name'])}",
        "type": "BRANCH_PERFORMANCE",
        "severity": severity,
        "title": f"{branch['branch_name']} apresenta atraso acima da média",
        "summary": (
            f"A filial está {_pt_number(gap)} pontos percentuais acima da taxa geral."
        ),
        "reference_date": DEMO_REFERENCE_DATE,
        "metrics": [
            {
                "label": "Taxa da filial",
                "value": branch["delay_rate"],
                "unit": "percentage",
            },
            {"label": "Taxa geral", "value": overall_rate, "unit": "percentage"},
            {"label": "Pedidos recentes", "value": branch["total_orders"], "unit": "count"},
        ],
        "context": {"branch_id": branch["branch_id"]},
    }


def inventory_risk_rule(items: list[dict]) -> dict | None:
    if not items:
        return None

    occurrences = len(items)
    product_count = len({item["product_id"] for item in items})
    total_deficit = sum(item["deficit"] for item in items)
    related_delays = sum(item.get("delayed_orders", 0) for item in items)
    if occurrences >= INVENTORY_CRITICAL_OCCURRENCES:
        severity = "critical"
    elif (
        occurrences >= INVENTORY_HIGH_OCCURRENCES
        or related_delays >= INVENTORY_HIGH_RELATED_DELAYS
    ):
        severity = "high"
    else:
        severity = "medium"

    return {
        "key": "inventory-risk",
        "type": "INVENTORY_RISK",
        "severity": severity,
        "title": "Produtos com estoque abaixo do mínimo",
        "summary": (
            f"Foram identificadas {occurrences} combinações de filial e produto em "
            "condição crítica."
        ),
        "reference_date": DEMO_REFERENCE_DATE,
        "metrics": [
            {"label": "Ocorrências", "value": occurrences, "unit": "count"},
            {"label": "Produtos", "value": product_count, "unit": "count"},
            {"label": "Déficit total", "value": total_deficit, "unit": "count"},
        ],
    }


def strategic_customer_risk_rule(customers: list[dict]) -> dict | None:
    affected = len(customers)
    if not affected:
        return None

    # Aqui a severidade acompanha o alcance do problema, não o valor de um cliente isolado.
    if affected >= STRATEGIC_CRITICAL_CUSTOMERS:
        severity = "critical"
    elif affected >= STRATEGIC_HIGH_CUSTOMERS:
        severity = "high"
    else:
        severity = "medium"

    return {
        "key": "strategic-customer-risk",
        "type": "STRATEGIC_CUSTOMER_RISK",
        "severity": severity,
        "title": "Clientes estratégicos apresentam ocorrências recorrentes",
        "summary": (
            f"{affected} clientes estratégicos registraram atrasos ou chamados recorrentes."
        ),
        "reference_date": DEMO_REFERENCE_DATE,
        "metrics": [
            {"label": "Clientes afetados", "value": affected, "unit": "count"},
            {
                "label": "Atrasos recentes",
                "value": sum(customer["recent_delays"] for customer in customers),
                "unit": "count",
            },
            {
                "label": "Chamados recentes",
                "value": sum(customer["recent_tickets"] for customer in customers),
                "unit": "count",
            },
        ],
    }
