from decimal import Decimal

from django.utils.dateparse import parse_datetime

from operations.models import Branch, Customer, Product
from operations.ingestion.types import CleanOrder, CleanOrderItem


def transform_orders(records: list[dict]) -> list[CleanOrder]:
    """Converte o CLEAN validado nos tipos usados pelo domínio BUSINESS."""
    branches = {item.name: item for item in Branch.objects.all()}
    customers = {item.name: item for item in Customer.objects.all()}
    products = {item.sku: item for item in Product.objects.all()}
    transformed = []
    for record in records:
        items = tuple(
            CleanOrderItem(
                product=products[item["sku"].strip()],
                quantity=item["quantity"],
                unit_price=Decimal(str(item["unit_price"])).quantize(Decimal("0.01")),
            )
            for item in record["items"]
        )
        transformed.append(CleanOrder(
            external_id=record["external_id"].strip(),
            customer=customers[record["customer"].strip()],
            branch=branches[record["branch"].strip()],
            created_at=parse_datetime(record["created_at"]),
            promised_at=parse_datetime(record["promised_at"]),
            delivered_at=parse_datetime(record["delivered_at"]) if record.get("delivered_at") else None,
            status=record["status"].strip(),
            total_amount=Decimal(str(record["total_amount"])).quantize(Decimal("0.01")),
            items=items,
        ))
    return transformed
