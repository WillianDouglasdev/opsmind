from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db.models import Sum
from rest_framework.test import APIClient

from operations.analytics.dashboard import (
    build_dashboard_changes,
    build_dashboard_summary,
    build_dashboard_trends,
    calculate_operational_health,
)
from operations.analytics.queries import (
    VALID_REVENUE_STATUSES,
    branch_delay_rates,
    comparison_periods,
    critical_inventory_items,
    delay_metrics,
    delivery_ticket_metrics,
    percentage_change,
    recurring_strategic_customers,
)
from operations.models import Order

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def full_demo(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("seed_demo", reset=True, verbosity=0)
    yield
    with django_db_blocker.unblock():
        call_command("flush", interactive=False, verbosity=0)


def test_percentage_change_handles_zero_and_regular_values() -> None:
    assert percentage_change(120, 100) == 20.0
    assert percentage_change(0, 0) == 0.0
    assert percentage_change(10, 0) is None


def test_summary_uses_database_values(full_demo) -> None:
    summary = build_dashboard_summary()
    current_start, current_end = comparison_periods()["current"]
    expected_revenue = (
        Order.objects.filter(
            status__in=VALID_REVENUE_STATUSES,
            created_at__gte=current_start,
            created_at__lte=current_end,
        ).aggregate(value=Sum("total_amount"))["value"]
    ).quantize(Decimal("0.01"))

    assert summary["revenue"]["value"] == expected_revenue
    assert summary["orders"]["value"] == 431
    assert summary["delayed_orders"]["value"] == 60
    assert summary["delayed_orders"]["rate"] > 0
    assert summary["open_tickets"]["value"] > 0
    assert 0 <= summary["operational_health"]["score"] <= 100


def test_health_score_respects_limits() -> None:
    healthy_metrics = {
        "delay_rate": 0,
        "delay_growth": 0,
        "critical_inventory_rate": 0,
        "active_ticket_rate": 0,
        "strategic_customer_rate": 0,
        "worst_branch_gap": 0,
    }
    stressed_metrics = {name: 1000 for name in healthy_metrics}

    assert calculate_operational_health(healthy_metrics)["score"] == 100
    assert 0 <= calculate_operational_health(stressed_metrics)["score"] <= 100


def test_demo_preserves_expected_operational_patterns(full_demo) -> None:
    delays = delay_metrics()
    branches = branch_delay_rates()
    critical_skus = {item["product__sku"] for item in critical_inventory_items()}
    tickets = delivery_ticket_metrics()
    strategic_customers = recurring_strategic_customers()
    contagem = next(branch for branch in branches if branch["branch_name"] == "Contagem")

    assert delays["rate"] > delays["previous_rate"]
    assert delays["change_percentage"] > 0
    assert contagem["delay_rate"] > delays["rate"]
    assert {"P018", "P027"}.issubset(critical_skus)
    assert tickets["value"] > tickets["previous_value"]
    assert strategic_customers
    assert all(
        customer["recent_delays"] >= 2 or customer["recent_tickets"] >= 2
        for customer in strategic_customers
    )


def test_monthly_trends_are_real_rates_for_six_months(full_demo) -> None:
    trends = build_dashboard_trends()

    assert trends["metric"] == "on_time_delivery_rate"
    assert trends["target"] == 90.0
    assert [point["month"] for point in trends["series"]] == [
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
    ]
    assert all(0 <= point["value"] <= 100 for point in trends["series"])
    assert all(point["total_orders"] > 0 for point in trends["series"])


def test_changes_distinguish_percentages_from_inventory_snapshot(full_demo) -> None:
    changes = build_dashboard_changes()["items"]
    inventory_change = next(item for item in changes if item["type"] == "inventory")

    assert len(changes) == 4
    assert inventory_change["direction"] == "current"
    assert inventory_change["value"] == 4
    assert "%" not in inventory_change["description"]


@pytest.mark.parametrize(
    ("path", "required_keys"),
    [
        (
            "/api/dashboard/summary/",
            {"reference_date", "operational_health", "revenue", "orders", "delayed_orders"},
        ),
        ("/api/dashboard/trends/", {"reference_date", "metric", "target", "series"}),
        ("/api/dashboard/changes/", {"reference_date", "items"}),
    ],
)
def test_dashboard_endpoints_return_expected_contract(
    full_demo,
    path: str,
    required_keys: set[str],
) -> None:
    response = APIClient().get(path)

    assert response.status_code == 200
    assert required_keys.issubset(response.json())

