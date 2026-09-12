from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from operations.investigations import (
    build_delivery_delay_investigation,
    list_investigations,
)
from operations.models import Branch, Customer, Inventory, Order, OrderItem, Product, Ticket

pytestmark = pytest.mark.django_db


def at(day: int, hour: int = 10):
    return timezone.make_aware(datetime(2026, 8, day, hour))


def create_order(branch, customer, status, amount, created_at):
    return Order.objects.create(
        branch=branch,
        customer=customer,
        status=status,
        created_at=created_at,
        promised_at=created_at + timedelta(days=2),
        total_amount=Decimal(amount),
    )


@pytest.fixture
def investigation_data():
    contagem = Branch.objects.create(name="Contagem", city="Contagem", state="MG")
    betim = Branch.objects.create(name="Betim", city="Betim", state="MG")
    strategic = Customer.objects.create(
        name="Cliente estratégico",
        segment=Customer.Segment.STRATEGIC,
        city="Contagem",
        state="MG",
    )
    retail = Customer.objects.create(
        name="Cliente varejo",
        segment=Customer.Segment.RETAIL,
        city="Betim",
        state="MG",
    )
    product = Product.objects.create(
        sku="P018",
        name="Componente crítico",
        category=Product.Category.SUPPLIES,
        unit_price=Decimal("25.00"),
    )
    Inventory.objects.create(
        branch=contagem,
        product=product,
        current_quantity=2,
        minimum_quantity=10,
    )

    delayed_one = create_order(
        contagem, strategic, Order.Status.DELAYED, "100.00", at(10)
    )
    delayed_two = create_order(
        contagem, strategic, Order.Status.DELAYED, "200.00", at(11)
    )
    create_order(contagem, retail, Order.Status.DELIVERED, "300.00", at(12))
    create_order(betim, retail, Order.Status.DELAYED, "80.00", at(13))
    create_order(betim, retail, Order.Status.DELIVERED, "120.00", at(14))
    create_order(
        contagem,
        strategic,
        Order.Status.DELIVERED,
        "50.00",
        at(10) - timedelta(days=30),
    )

    OrderItem.objects.create(
        order=delayed_one,
        product=product,
        quantity=2,
        unit_price=Decimal("25.00"),
    )
    OrderItem.objects.create(
        order=delayed_two,
        product=product,
        quantity=1,
        unit_price=Decimal("25.00"),
    )
    Ticket.objects.create(
        customer=strategic,
        order=delayed_one,
        category=Ticket.Category.DELIVERY,
        priority=Ticket.Priority.HIGH,
        description="Pedido atrasado",
        status=Ticket.Status.OPEN,
        created_at=at(15),
    )
    Ticket.objects.create(
        customer=strategic,
        order=delayed_two,
        category=Ticket.Category.DELIVERY,
        priority=Ticket.Priority.MEDIUM,
        description="Prazo de entrega",
        status=Ticket.Status.IN_PROGRESS,
        created_at=at(16),
    )
    return {"contagem": contagem, "betim": betim}


def test_lists_only_the_available_delivery_investigation(investigation_data):
    payload = list_investigations(days=30)

    assert len(payload["items"]) == 1
    assert payload["items"][0]["type"] == "delivery_delays"
    assert payload["items"][0]["branch"]["name"] == "Contagem"
    assert "branch=" in payload["items"][0]["detail_url"]


def test_delivery_investigation_compares_branch_with_operation(investigation_data):
    payload = build_delivery_delay_investigation(
        days=30,
        branch_id=investigation_data["contagem"].pk,
    )
    summary = payload["summary"]

    assert summary["branch"]["name"] == "Contagem"
    assert summary["branch_delay_rate"] == 66.67
    assert summary["operation_delay_rate"] == 60.0
    assert summary["difference_percentage_points"] == 6.67
    assert summary["delayed_orders"] == 2
    assert summary["affected_revenue"] == Decimal("300.00")


def test_general_detail_selects_the_most_affected_branch(investigation_data):
    response = APIClient().get("/api/investigations/delivery-delays/?days=30")

    assert response.status_code == 200
    assert response.json()["summary"]["branch"]["name"] == "Contagem"


def test_investigation_composes_tickets_inventory_and_strategic_customers(
    investigation_data,
):
    payload = build_delivery_delay_investigation(
        branch_id=investigation_data["contagem"].pk
    )
    evidence_by_type = {item["type"]: item for item in payload["evidence"]}

    assert evidence_by_type["tickets"]["current"]["value"] == 2
    assert evidence_by_type["tickets"]["comparison"]["value"] == 0
    assert evidence_by_type["tickets"]["difference"]["value"] == 2
    assert evidence_by_type["tickets"]["change"]["value"] is None
    assert evidence_by_type["inventory"]["title"].startswith("P018")
    assert evidence_by_type["inventory"]["current"]["value"] == 2
    assert evidence_by_type["customers"]["current"]["value"] == 1
    assert evidence_by_type["customers"]["comparison"]["value"] == 2


def test_timeline_and_next_steps_are_derived_from_available_signals(investigation_data):
    payload = build_delivery_delay_investigation(
        branch_id=investigation_data["contagem"].pk
    )
    step_keys = {item["key"] for item in payload["next_steps"]}

    assert [item["value"] for item in payload["timeline"]] == [1, 1]
    assert {
        "review-delayed-orders",
        "review-delivery-tickets",
        "review-related-inventory",
        "prioritize-strategic-customers",
        "compare-branches",
    } == step_keys


def test_no_additional_evidence_is_a_valid_partial_result():
    branch = Branch.objects.create(name="Betim", city="Betim", state="MG")
    customer = Customer.objects.create(
        name="Cliente varejo",
        segment=Customer.Segment.RETAIL,
        city="Betim",
        state="MG",
    )
    create_order(branch, customer, Order.Status.DELAYED, "100.00", at(12))

    payload = build_delivery_delay_investigation(branch_id=branch.pk)

    assert payload["data_status"] == "partial"
    assert {item["type"] for item in payload["evidence"]} == {"delivery"}
    assert {item["key"] for item in payload["next_steps"]} == {
        "review-delayed-orders",
        "compare-branches",
    }


def test_absence_of_delays_returns_empty_payload():
    assert list_investigations()["items"] == []
    payload = build_delivery_delay_investigation()
    assert payload["data_status"] == "empty"
    assert payload["summary"] is None
    assert payload["evidence"] == []


def test_unknown_branch_returns_404(investigation_data):
    response = APIClient().get(
        "/api/investigations/delivery-delays/?days=30&branch=99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Filial não encontrada."


def test_investigation_text_does_not_claim_causality(investigation_data):
    payload = build_delivery_delay_investigation(
        branch_id=investigation_data["contagem"].pk
    )
    text = str(payload).lower()

    assert "causou o atraso" not in text
    assert "provocou o atraso" not in text
    assert "não confirmam relações de causa e efeito" in payload["causality_notice"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/investigations/?days=8",
        "/api/investigations/?branch=1",
        "/api/investigations/delivery-delays/?days=abc",
        "/api/investigations/delivery-delays/?branch=abc",
        "/api/investigations/delivery-delays/?unknown=value",
    ],
)
def test_invalid_investigation_parameters_return_400(path, investigation_data):
    assert APIClient().get(path).status_code == 400
