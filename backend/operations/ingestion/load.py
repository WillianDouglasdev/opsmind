from django.db import transaction

from operations.models import Order, OrderItem
from operations.ingestion.types import CleanOrder

SOURCE_SYSTEM = "demo_erp"


def load_orders(orders: list[CleanOrder]) -> int:
    """Publica o lote inteiro; uma falha desfaz pedidos e itens desta execução."""
    with transaction.atomic():
        for clean in orders:
            # A origem + external_id é a chave de idempotência. Atualizamos o cabeçalho
            # e substituímos seus itens na mesma transação para manter total e linhas juntos.
            order, _created = Order.objects.update_or_create(
                source_system=SOURCE_SYSTEM,
                external_id=clean.external_id,
                defaults={
                    "customer": clean.customer,
                    "branch": clean.branch,
                    "created_at": clean.created_at,
                    "promised_at": clean.promised_at,
                    "delivered_at": clean.delivered_at,
                    "status": clean.status,
                    "total_amount": clean.total_amount,
                },
            )
            order.items.all().delete()
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
                for item in clean.items
            ])
    return len(orders)
