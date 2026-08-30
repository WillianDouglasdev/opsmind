from decimal import Decimal

import pytest
from django.core.management import call_command

from operations.models import ActionItem, Branch, Customer, Inventory, Order, Product, Ticket


@pytest.mark.django_db(transaction=True)
def test_small_seed_creates_data_without_duplicating_on_second_run() -> None:
    call_command("seed_demo", reset=True, small=True, verbosity=0)

    first_counts = {
        "branches": Branch.objects.count(),
        "customers": Customer.objects.count(),
        "products": Product.objects.count(),
        "inventory": Inventory.objects.count(),
        "orders": Order.objects.count(),
        "tickets": Ticket.objects.count(),
    }

    call_command("seed_demo", small=True, verbosity=0)

    assert first_counts["branches"] == 5
    assert first_counts["customers"] > 0
    assert first_counts["products"] >= 27
    assert first_counts["inventory"] == first_counts["branches"] * first_counts["products"]
    assert first_counts["orders"] > 0
    assert first_counts["tickets"] > 0
    assert Branch.objects.count() == first_counts["branches"]
    assert Order.objects.count() == first_counts["orders"]

    for order in Order.objects.prefetch_related("items"):
        calculated_total = sum(
            (item.unit_price * item.quantity for item in order.items.all()),
            Decimal("0.00"),
        )
        assert order.total_amount == calculated_total

    ActionItem.objects.create(
        recommendation_key="acao-de-teste",
        title="Ação de teste",
        description="Registro usado para validar o reset da demonstração.",
        source_alert_key="alerta-de-teste",
        source_alert_type="TEST_ALERT",
        priority=ActionItem.Priority.LOW,
    )
    call_command("seed_demo", reset=True, small=True, verbosity=0)

    assert not ActionItem.objects.exists()
