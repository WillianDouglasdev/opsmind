from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from operations.models import Branch, Customer, Inventory, Order, OrderItem, Product, Ticket

pytestmark = pytest.mark.django_db


@pytest.fixture
def branch() -> Branch:
    return Branch.objects.create(name="Contagem", city="Contagem", state="MG")


@pytest.fixture
def customer() -> Customer:
    return Customer.objects.create(
        name="Cliente Sintético",
        segment=Customer.Segment.CORPORATE,
        city="Betim",
        state="MG",
        status=Customer.Status.ACTIVE,
    )


@pytest.fixture
def product() -> Product:
    return Product.objects.create(
        sku="P001",
        name="Produto de Teste",
        category=Product.Category.EQUIPMENT,
        unit_price=Decimal("199.90"),
    )


@pytest.fixture
def order(branch: Branch, customer: Customer) -> Order:
    created_at = timezone.now()
    return Order.objects.create(
        customer=customer,
        branch=branch,
        created_at=created_at,
        promised_at=created_at + timedelta(days=5),
        status=Order.Status.PROCESSING,
        total_amount=Decimal("0.00"),
    )


def test_product_sku_is_unique(product: Product) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.create(
            sku=product.sku,
            name="Outro produto",
            category=Product.Category.OFFICE,
            unit_price=Decimal("25.00"),
        )


def test_inventory_is_unique_per_branch_and_product(
    branch: Branch,
    product: Product,
) -> None:
    Inventory.objects.create(
        branch=branch,
        product=product,
        current_quantity=20,
        minimum_quantity=10,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Inventory.objects.create(
            branch=branch,
            product=product,
            current_quantity=30,
            minimum_quantity=10,
        )


def test_inventory_rejects_negative_quantity(
    branch: Branch,
    product: Product,
) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Inventory.objects.create(
            branch=branch,
            product=product,
            current_quantity=-1,
            minimum_quantity=10,
        )


def test_order_item_quantity_must_be_positive(order: Order, product: Product) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=0,
            unit_price=product.unit_price,
        )


def test_money_values_use_decimal_and_keep_sale_price(
    order: Order,
    product: Product,
) -> None:
    item = OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        unit_price=product.unit_price,
    )
    original_sale_price = item.unit_price

    product.unit_price = Decimal("249.90")
    product.save(update_fields=["unit_price"])
    item.refresh_from_db()

    assert isinstance(item.unit_price, Decimal)
    assert item.unit_price == original_sale_price
    assert isinstance(order.total_amount, Decimal)


def test_deleting_order_removes_items_and_preserves_ticket(
    order: Order,
    product: Product,
    customer: Customer,
) -> None:
    item = OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        unit_price=product.unit_price,
    )
    ticket = Ticket.objects.create(
        customer=customer,
        order=order,
        category=Ticket.Category.DELIVERY,
        priority=Ticket.Priority.MEDIUM,
        description="Chamado sintético para validar o relacionamento.",
        status=Ticket.Status.OPEN,
    )

    order.delete()
    ticket.refresh_from_db()

    assert not OrderItem.objects.filter(pk=item.pk).exists()
    assert ticket.order is None


def test_product_used_in_order_item_is_protected(
    order: Order,
    product: Product,
) -> None:
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        unit_price=product.unit_price,
    )

    with pytest.raises(ProtectedError):
        product.delete()
