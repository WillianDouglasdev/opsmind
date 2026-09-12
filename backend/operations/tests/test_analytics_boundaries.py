"""Protege o contrato atual de ingestão com exemplos pequenos, sem chamar o seed."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from operations.analytics.queries import branch_delay_rates, delay_metrics, order_metrics, revenue_metrics
from operations.models import Branch, Customer, Order

pytestmark = pytest.mark.django_db
REFERENCE_DATE = date(2026, 8, 29)


def at(year, month, day, hour=12):
    return timezone.make_aware(datetime(year, month, day, hour))


@pytest.fixture
def make_order():
    branch = Branch.objects.create(name="Filial de teste", city="Betim", state="MG")
    customer = Customer.objects.create(
        name="Cliente de teste", segment=Customer.Segment.RETAIL, city="Betim", state="MG"
    )

    def create(created_at, status=Order.Status.DELIVERED, amount="10.00", **fields):
        return Order.objects.create(
            branch=branch,
            customer=customer,
            created_at=created_at,
            promised_at=created_at + timedelta(days=1),
            status=status,
            total_amount=Decimal(amount),
            **fields,
        )

    return create


def test_comparison_windows_include_each_boundary_once(make_order):
    # Para 29/08: período atual começa em 31/07; anterior começa em 01/07.
    # Valores diferentes ajudam a detectar dupla contagem e limites invertidos.
    make_order(at(2026, 6, 30, 23), amount="1.00")
    make_order(at(2026, 7, 1, 0), amount="2.00")
    make_order(at(2026, 7, 30, 23), amount="4.00")
    make_order(at(2026, 7, 31, 0), amount="8.00")
    make_order(at(2026, 8, 29, 23), amount="16.00")
    make_order(at(2026, 8, 30, 0), amount="32.00")

    orders = order_metrics(REFERENCE_DATE)
    revenue = revenue_metrics(REFERENCE_DATE)

    assert (orders["value"], orders["previous_value"]) == (2, 2)
    assert revenue["value"] == Decimal("24.00")
    assert revenue["previous_value"] == Decimal("6.00")


def test_cancelled_orders_count_in_volume_but_not_revenue(make_order):
    make_order(at(2026, 8, 1), amount="12.34")
    make_order(at(2026, 8, 1), status=Order.Status.CANCELLED, amount="99.99")

    assert order_metrics(REFERENCE_DATE)["value"] == 2
    assert revenue_metrics(REFERENCE_DATE)["value"] == Decimal("12.34")


def test_branch_rates_use_the_same_timezone_boundary_as_order_metrics(make_order):
    make_order(at(2026, 7, 30, 23), status=Order.Status.DELAYED)
    make_order(at(2026, 7, 31, 0), status=Order.Status.DELAYED)
    make_order(at(2026, 8, 29, 23), status=Order.Status.DELIVERED)

    branch = branch_delay_rates(REFERENCE_DATE)[0]
    orders = order_metrics(REFERENCE_DATE)

    assert branch["total_orders"] == orders["value"] == 2
    assert branch["delayed_orders"] == 1
    assert branch["delay_rate"] == 50.0


def test_delay_metric_reads_status_instead_of_inferring_it_from_dates(make_order):
    # Na regra atual, até uma entrega tardia só entra no KPI se tiver status delayed.
    # Este teste torna explícito o contrato que uma futura carga terá de respeitar.
    make_order(at(2026, 8, 1), delivered_at=at(2026, 8, 4))
    make_order(at(2026, 8, 1), status=Order.Status.DELAYED, delivered_at=at(2026, 8, 4))
    make_order(at(2026, 8, 1), status=Order.Status.SHIPPED)
    make_order(at(2026, 8, 1), status=Order.Status.CANCELLED)

    delays = delay_metrics(REFERENCE_DATE)

    assert delays["value"] == 1
    assert delays["rate"] == 25.0
    assert delays["change_percentage"] is None


def test_empty_period_has_zero_totals_without_inventing_growth():
    assert order_metrics(REFERENCE_DATE)["value"] == 0
    assert revenue_metrics(REFERENCE_DATE)["value"] == Decimal("0.00")
    delays = delay_metrics(REFERENCE_DATE)
    assert delays["rate"] == 0.0
    assert delays["change_percentage"] == 0.0
