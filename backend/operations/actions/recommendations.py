from operations.alerts.investigations import build_investigation


def _pt_number(value) -> str:
    return f"{float(value):.2f}".replace(".", ",")


def _currency(value) -> str:
    formatted = f"{float(value):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


def _leading_priority(alert: dict) -> str:
    return "critical" if alert["severity"] == "critical" else "high"


def _delivery_recommendations(investigation: dict) -> list[dict]:
    # Os textos podem mudar sem afetar os dados estruturados usados nas recomendações.
    alert = investigation["alert"]
    context = investigation["_recommendation_context"]
    impact = context["impact"]
    branch = context["worst_branch"]
    tickets = context["tickets"]
    branch_name = branch["branch_name"]
    return [
        {
            "recommendation_key": "review-high-impact-delays",
            "title": "Revisar pedidos atrasados de maior impacto",
            "description": (
                "Priorizar a análise dos pedidos atrasados com maior valor financeiro "
                "ou clientes estratégicos."
            ),
            "priority": _leading_priority(alert),
            "reason": (
                f"{impact['delayed_orders']} pedidos atrasados afetam "
                f"{impact['impacted_customers']} clientes e representam "
                f"{_currency(impact['affected_revenue'])}."
            ),
        },
        {
            "recommendation_key": "review-worst-branch",
            "title": f"Revisar operação da filial {branch_name}",
            "description": (
                "Investigar capacidade e fluxo operacional da filial que apresenta "
                "desempenho abaixo da média."
            ),
            "priority": "high",
            "reason": (
                f"A filial apresenta taxa de atraso de "
                f"{_pt_number(branch['delay_rate'])}%, com "
                f"{branch['delayed_orders']} pedidos atrasados."
            ),
        },
        {
            "recommendation_key": "monitor-delivery-tickets",
            "title": "Monitorar chamados relacionados a entrega",
            "description": (
                "Acompanhar os chamados de entrega enquanto a taxa de atraso permanecer elevada."
            ),
            "priority": "medium",
            "reason": (
                f"Os chamados de entrega passaram de "
                f"{tickets['previous_value']} para "
                f"{tickets['value']}, variação de "
                f"{_pt_number(tickets['change_percentage'])}%."
            ),
        },
    ]


def _branch_recommendations(investigation: dict) -> list[dict]:
    alert = investigation["alert"]
    context = investigation["_recommendation_context"]
    branch = context["branch"]
    branch_name = branch["branch_name"]
    product_skus = [product["sku"] for product in context["products"][:3]]
    products = ", ".join(product_skus)
    return [
        {
            "recommendation_key": "review-branch-flow",
            "title": f"Revisar fluxo operacional da filial {branch_name}",
            "description": (
                "Analisar capacidade, etapas e concentração do fluxo recente da unidade."
            ),
            "priority": _leading_priority(alert),
            "reason": (
                f"A taxa de atraso da filial é "
                f"{_pt_number(branch['delay_rate'])}%, "
                f"{_pt_number(context['gap'])} p.p. acima da média."
            ),
        },
        {
            "recommendation_key": "review-branch-delayed-orders",
            "title": f"Analisar pedidos atrasados concentrados em {branch_name}",
            "description": (
                "Revisar os pedidos atrasados da unidade e identificar concentrações operacionais."
            ),
            "priority": "high",
            "reason": (
                f"A filial reúne {branch['delayed_orders']} atrasos entre "
                f"{branch['total_orders']} pedidos recentes."
            ),
        },
        {
            "recommendation_key": "review-branch-products",
            "title": f"Revisar produtos associados aos atrasos de {branch_name}",
            "description": (
                "Analisar os produtos mais presentes nos pedidos atrasados recentes da filial."
            ),
            "priority": "medium",
            "reason": (
                f"Os produtos com maior presença nas evidências da filial são {products}."
                if products
                else "Não há produtos suficientes para detalhar este sinal."
            ),
        },
    ]


def _inventory_recommendations(investigation: dict) -> list[dict]:
    alert = investigation["alert"]
    context = investigation["_recommendation_context"]
    items = context["items"]
    # dict.fromkeys remove SKUs repetidos sem perder a ordem calculada pela análise.
    skus = list(dict.fromkeys(item["product__sku"] for item in items))
    sku_text = " e ".join(skus)
    largest = sorted(
        items,
        key=lambda item: item["deficit"],
        reverse=True,
    )[:2]
    deficit_text = ", ".join(
        f"{item['product__sku']} em {item['branch__name']}"
        for item in largest
    )
    return [
        {
            "recommendation_key": "review-critical-inventory",
            "title": f"Revisar reposição de {sku_text}",
            "description": (
                "Revisar a reposição dos produtos identificados abaixo do estoque mínimo."
            ),
            "priority": _leading_priority(alert),
            "reason": (
                f"Foram identificadas {len(items)} ocorrências, com déficit total de "
                f"{context['total_deficit']} unidades."
            ),
        },
        {
            "recommendation_key": "prioritize-largest-inventory-deficits",
            "title": "Priorizar produtos com maior déficit de estoque",
            "description": (
                "Concentrar a análise inicial nas combinações de produto e filial com maior déficit."
            ),
            "priority": "high",
            "reason": f"Os maiores déficits atuais aparecem em {deficit_text}.",
        },
        {
            "recommendation_key": "review-inventory-related-orders",
            "title": "Verificar pedidos relacionados aos produtos críticos",
            "description": (
                "Revisar pedidos atrasados que contenham produtos atualmente abaixo do mínimo."
            ),
            "priority": "medium",
            "reason": (
                f"{context['related_orders']} pedidos atrasados "
                "estão relacionados aos produtos críticos; o sinal não comprova causalidade."
            ),
        },
    ]


def _customer_recommendations(investigation: dict) -> list[dict]:
    alert = investigation["alert"]
    context = investigation["_recommendation_context"]
    names = [customer["name"] for customer in context["customers"][:2]]
    name_text = " e ".join(names)
    return [
        {
            "recommendation_key": "review-strategic-customers",
            "title": "Revisar clientes estratégicos com ocorrências recorrentes",
            "description": (
                "Analisar os clientes estratégicos que concentram atrasos ou chamados recentes."
            ),
            "priority": _leading_priority(alert),
            "reason": (
                f"{context['affected_customers']} clientes estratégicos concentram "
                f"{context['delayed_orders']} atrasos e "
                f"{context['tickets']} chamados."
            ),
        },
        {
            "recommendation_key": "prioritize-high-impact-customers",
            "title": "Priorizar clientes estratégicos de maior impacto",
            "description": (
                "Priorizar a revisão dos clientes com maior recorrência de sinais no período."
            ),
            "priority": "high",
            "reason": f"{name_text} lideram as ocorrências recorrentes nas evidências atuais.",
        },
        {
            "recommendation_key": "monitor-strategic-customer-cases",
            "title": "Acompanhar pedidos e chamados dos clientes afetados",
            "description": (
                "Acompanhar a evolução dos pedidos e chamados associados aos clientes identificados."
            ),
            "priority": "medium",
            "reason": (
                f"O grupo afetado representa {_currency(context['revenue'])} "
                "de faturamento no período."
            ),
        },
    ]


RECOMMENDATION_BUILDERS = {
    "DELIVERY_DELAY_INCREASE": _delivery_recommendations,
    "BRANCH_PERFORMANCE": _branch_recommendations,
    "INVENTORY_RISK": _inventory_recommendations,
    "STRATEGIC_CUSTOMER_RISK": _customer_recommendations,
}


def build_recommendations(alert_key: str) -> list[dict]:
    # Não usamos o LLM aqui porque ações disponíveis precisam continuar previsíveis.
    investigation = build_investigation(alert_key)
    alert = investigation["alert"]
    recommendations = RECOMMENDATION_BUILDERS[alert["type"]](investigation)
    return [
        {
            **recommendation,
            "alert_key": alert["key"],
            "alert_type": alert["type"],
        }
        for recommendation in recommendations
    ]
