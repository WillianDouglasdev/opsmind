import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from operations.alerts.engine import get_active_alerts, sort_alerts
from operations.alerts.investigations import build_investigation
from operations.alerts.rules import (
    branch_performance_rule,
    delivery_delay_rule,
    inventory_risk_rule,
    strategic_customer_risk_rule,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def full_demo(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("seed_demo", reset=True, verbosity=0)
    yield
    with django_db_blocker.unblock():
        call_command("flush", interactive=False, verbosity=0)


def test_delivery_rule_requires_thresholds_and_sets_severity() -> None:
    below_threshold = {"rate": 9.9, "previous_rate": 8.0, "change_percentage": 23.75}
    medium = {"rate": 12.0, "previous_rate": 10.3, "change_percentage": 16.5}
    high = {"rate": 13.9, "previous_rate": 11.2, "change_percentage": 24.1}

    assert delivery_delay_rule(below_threshold) is None
    assert delivery_delay_rule(medium)["severity"] == "medium"
    assert delivery_delay_rule(high)["severity"] == "high"


def test_branch_rule_requires_relevant_volume() -> None:
    small_branch = {
        "branch_id": 1,
        "branch_name": "Filial pequena",
        "total_orders": 10,
        "delayed_orders": 3,
        "delay_rate": 30.0,
    }
    relevant_branch = {**small_branch, "total_orders": 100, "delay_rate": 21.0}

    assert branch_performance_rule(small_branch, 13.0) is None
    assert branch_performance_rule(relevant_branch, 13.0)["severity"] == "high"


def test_inventory_and_strategic_rules_are_consolidated() -> None:
    inventory_items = [
        {"product_id": index, "deficit": 5, "delayed_orders": 2}
        for index in range(4)
    ]
    customers = [
        {"recent_delays": 2, "recent_tickets": 1}
        for _index in range(5)
    ]

    assert inventory_risk_rule([]) is None
    assert inventory_risk_rule(inventory_items)["key"] == "inventory-risk"
    assert strategic_customer_risk_rule([]) is None
    assert strategic_customer_risk_rule(customers)["severity"] == "high"


def test_engine_orders_alerts_by_severity() -> None:
    alerts = [
        {"key": "low", "severity": "low"},
        {"key": "critical", "severity": "critical"},
        {"key": "medium", "severity": "medium"},
        {"key": "high", "severity": "high"},
    ]

    assert [alert["severity"] for alert in sort_alerts(alerts)] == [
        "critical",
        "high",
        "medium",
        "low",
    ]


def test_demo_detects_four_expected_alert_categories(full_demo) -> None:
    alerts = get_active_alerts()
    alert_types = {alert["type"] for alert in alerts}
    branch_alert = next(alert for alert in alerts if alert["type"] == "BRANCH_PERFORMANCE")

    assert alert_types == {
        "DELIVERY_DELAY_INCREASE",
        "BRANCH_PERFORMANCE",
        "INVENTORY_RISK",
        "STRATEGIC_CUSTOMER_RISK",
    }
    assert branch_alert["title"].startswith("Contagem")


def test_demo_investigations_include_expected_evidence(full_demo) -> None:
    inventory = build_investigation("inventory-risk")
    delivery = build_investigation("delivery-delay-increase")
    strategic = build_investigation("strategic-customer-risk")
    inventory_titles = {evidence["title"].split(" — ")[0] for evidence in inventory["evidence"]}
    ticket_signal = next(
        signal for signal in delivery["related_signals"] if signal["title"] == "Chamados de entrega"
    )
    ticket_values = {metric["label"]: metric["value"] for metric in ticket_signal["metrics"]}

    assert {"P018", "P027"}.issubset(inventory_titles)
    assert ticket_values["Chamados recentes"] > ticket_values["Período anterior"]
    assert strategic["impact"][0]["value"] > 0
    assert all(evidence["metrics"] for evidence in inventory["evidence"])


def test_alert_endpoints_and_not_found_contract(full_demo) -> None:
    client = APIClient()
    list_response = client.get("/api/alerts/")
    investigation_response = client.get("/api/alerts/delivery-delay-increase/investigation/")
    missing_response = client.get("/api/alerts/alerta-inexistente/investigation/")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 4
    assert {"key", "severity", "title", "summary", "metrics"}.issubset(
        list_response.json()[0]
    )
    assert investigation_response.status_code == 200
    assert {"alert", "impact", "evidence", "related_signals", "context"}.issubset(
        investigation_response.json()
    )
    assert missing_response.status_code == 404
