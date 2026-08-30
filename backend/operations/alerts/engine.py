from operations.alerts.rules import (
    SEVERITY_ORDER,
    branch_performance_rule,
    delivery_delay_rule,
    inventory_risk_rule,
    strategic_customer_risk_rule,
)
from operations.analytics.queries import (
    branch_delay_rates,
    critical_inventory_signals,
    delay_metrics,
    recurring_strategic_customers,
)


def sort_alerts(alerts: list[dict]) -> list[dict]:
    return sorted(alerts, key=lambda alert: (SEVERITY_ORDER[alert["severity"]], alert["key"]))


def get_active_alerts() -> list[dict]:
    # Dashboard e alertas reaproveitam os mesmos analytics para não divergir nos números.
    delays = delay_metrics()
    alerts = []

    delay_alert = delivery_delay_rule(delays)
    if delay_alert:
        alerts.append(delay_alert)

    for branch in branch_delay_rates():
        branch_alert = branch_performance_rule(branch, delays["rate"])
        if branch_alert:
            alerts.append(branch_alert)

    inventory_alert = inventory_risk_rule(critical_inventory_signals())
    if inventory_alert:
        alerts.append(inventory_alert)

    strategic_alert = strategic_customer_risk_rule(recurring_strategic_customers())
    if strategic_alert:
        alerts.append(strategic_alert)

    # O engine só consolida regras ativas; não existe persistência de Alert nesta fase.
    return sort_alerts(alerts)


def get_alert(alert_key: str) -> dict | None:
    return next((alert for alert in get_active_alerts() if alert["key"] == alert_key), None)
