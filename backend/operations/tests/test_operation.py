from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from operations.models import Branch, Customer, Inventory, Order, Product, Ticket

pytestmark = pytest.mark.django_db


def at(day: int, hour: int = 10):
    return timezone.make_aware(datetime(2026, 8, day, hour))


@pytest.fixture
def operation_data():
    contagem = Branch.objects.create(name="Contagem", city="Contagem", state="MG")
    betim = Branch.objects.create(name="Betim", city="Betim", state="MG")
    empty = Branch.objects.create(name="Sem movimento", city="Belo Horizonte", state="MG")
    strategic = Customer.objects.create(
        name="Cliente estratégico", segment=Customer.Segment.STRATEGIC,
        city="Contagem", state="MG",
    )
    retail = Customer.objects.create(
        name="Cliente varejo", segment=Customer.Segment.RETAIL,
        city="Betim", state="MG",
    )
    product = Product.objects.create(
        sku="P001", name="Produto", category=Product.Category.SUPPLIES,
        unit_price=Decimal("10.00"),
    )
    Inventory.objects.create(
        branch=contagem, product=product, current_quantity=2, minimum_quantity=10,
    )
    Inventory.objects.create(
        branch=betim, product=product, current_quantity=20, minimum_quantity=10,
    )

    def order(branch, customer, status, amount, created_at=at(10)):
        delivered_at = created_at + timedelta(days=1) if status == Order.Status.DELIVERED else None
        return Order.objects.create(
            branch=branch, customer=customer, status=status,
            created_at=created_at, promised_at=created_at + timedelta(days=2),
            delivered_at=delivered_at, total_amount=Decimal(amount),
        )

    current = [
        order(contagem, strategic, Order.Status.DELAYED, "100.00"),
        order(contagem, strategic, Order.Status.DELAYED, "200.00", at(11)),
        order(contagem, retail, Order.Status.DELIVERED, "300.00", at(12)),
        order(contagem, retail, Order.Status.CANCELLED, "400.00", at(13)),
        order(betim, strategic, Order.Status.DELIVERED, "500.00", at(14)),
        order(betim, retail, Order.Status.PENDING, "600.00", at(15)),
    ]
    order(contagem, strategic, Order.Status.DELAYED, "50.00", at(10) - timedelta(days=30))
    order(contagem, retail, Order.Status.DELIVERED, "50.00", at(11) - timedelta(days=30))

    Ticket.objects.create(
        customer=strategic, order=current[0], category=Ticket.Category.DELIVERY,
        priority=Ticket.Priority.HIGH, description="Atraso", status=Ticket.Status.OPEN,
        created_at=at(16),
    )
    Ticket.objects.create(
        customer=retail, order=current[2], category=Ticket.Category.PRODUCT,
        priority=Ticket.Priority.LOW, description="Resolvido", status=Ticket.Status.RESOLVED,
        created_at=at(16), closed_at=at(17),
    )
    Ticket.objects.create(
        customer=retail, order=current[4], category=Ticket.Category.DELIVERY,
        priority=Ticket.Priority.MEDIUM, description="Em atendimento",
        status=Ticket.Status.IN_PROGRESS, created_at=at(16),
    )
    Ticket.objects.create(
        customer=strategic, category=Ticket.Category.SERVICE,
        priority=Ticket.Priority.LOW, description="Sem pedido", status=Ticket.Status.OPEN,
        created_at=at(16),
    )
    return {"contagem": contagem, "betim": betim, "empty": empty, "orders": current}


def test_operation_overview_lists_real_branch_metrics_and_empty_state(operation_data):
    response = APIClient().get("/api/operation/overview/?days=30")
    assert response.status_code == 200
    payload = response.json()
    assert payload["period"]["start_date"] == "2026-07-31"
    assert payload["metrics"] == {
        "orders": 6,
        "delayed_orders": 2,
        "delay_rate": 33.33,
        "revenue": "1700.00",
        "customers": 2,
        "active_tickets": 3,
        "critical_inventory": 1,
    }
    branches = {branch["name"]: branch for branch in payload["branches"]}
    assert branches["Contagem"]["delay_rate"] == 50.0
    assert branches["Contagem"]["revenue"] == "600.00"
    assert branches["Contagem"]["active_tickets"] == 1
    assert branches["Sem movimento"]["health"] is None
    assert payload["attention"]["critical_products"][0]["sku"] == "P001"


def test_branch_detail_compares_with_arithmetic_branch_average(operation_data):
    branch_id = operation_data["contagem"].pk
    response = APIClient().get(f"/api/operation/branches/{branch_id}/?days=30")
    assert response.status_code == 200
    payload = response.json()
    comparisons = {item["key"]: item for item in payload["comparisons"]}
    assert payload["branch"]["name"] == "Contagem"
    assert comparisons["delay_rate"] == {
        "key": "delay_rate", "label": "Atrasos", "unit": "percentage",
        "branch_value": 50.0, "average_value": 25.0, "difference": 25.0,
    }
    assert comparisons["orders"]["average_value"] == 2.0
    assert len(payload["trend"]) == 30
    assert sum(point["orders"] for point in payload["trend"]) == 4


def test_unknown_branch_returns_404(operation_data):
    response = APIClient().get("/api/operation/branches/99999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Filial não encontrada."


def test_delay_drill_down_returns_contribution_and_definition(operation_data):
    response = APIClient().get("/api/operation/delays/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"] == {
        "orders": 6, "delayed_orders": 2, "delay_rate": 33.33,
        "impacted_customers": 1,
    }
    assert payload["branches"][0]["name"] == "Contagem"
    assert payload["branches"][0]["contribution_percentage"] == 100.0
    assert payload["metric_definition"] == {
        "metric_key": "order_delay_rate", "entity": "orders", "field": "status",
        "rule": "status = delayed", "pipeline_key": "orders",
    }


def test_orders_are_paginated_and_expose_delivery_situation(operation_data):
    response = APIClient().get("/api/operation/orders/?page_size=2")
    assert response.status_code == 200
    payload = response.json()
    assert (payload["count"], payload["total_pages"], len(payload["results"])) == (6, 3, 2)
    assert {"identifier", "customer", "branch", "created_at", "total_amount", "status", "delivery_state"}.issubset(payload["results"][0])


def test_order_filters_combine_branch_status_and_delay(operation_data):
    client = APIClient()
    branch_id = operation_data["contagem"].pk
    delayed = client.get(f"/api/operation/orders/?branch={branch_id}&delivery=late").json()
    cancelled = client.get("/api/operation/orders/?status=cancelled").json()
    short_period = client.get("/api/operation/orders/?days=7").json()
    assert delayed["count"] == 2
    assert all(item["branch"]["id"] == branch_id and item["status"] == "delayed" for item in delayed["results"])
    assert cancelled["count"] == 1
    assert short_period["count"] == 0


@pytest.mark.parametrize("query", [
    "days=8", "status=unknown", "delivery=on_time", "page=0",
    "page_size=51", "branch=abc", "unknown=value",
])
def test_invalid_query_parameters_return_400(query, operation_data):
    response = APIClient().get(f"/api/operation/orders/?{query}")
    assert response.status_code == 400


def test_page_outside_result_returns_400(operation_data):
    response = APIClient().get("/api/operation/orders/?page=4&page_size=2")
    assert response.status_code == 400
    assert "página" in response.json()["detail"].lower()


def test_operation_without_branches_is_a_valid_empty_payload():
    response = APIClient().get("/api/operation/overview/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["branches"] == []
    assert payload["metrics"]["orders"] == 0
    assert payload["attention"]["worst_branch"] is None
