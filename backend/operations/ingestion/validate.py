from decimal import Decimal, InvalidOperation

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from operations.models import Branch, Customer, Order, Product
from operations.ingestion.types import RejectedRecord


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _datetime(value):
    parsed = parse_datetime(value) if isinstance(value, str) else None
    return parsed if parsed is not None and timezone.is_aware(parsed) else None


def _decimal(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return number if number.is_finite() else None


def _reject(identifier: str, code: str, message: str) -> RejectedRecord:
    return RejectedRecord(identifier or "Registro sem ID", code, message)


def validate_orders(records: list[dict]) -> tuple[list[dict], list[RejectedRecord]]:
    """Valida o CLEAN sem gravar; um registro ruim não interrompe os demais."""
    branches = {item.name: item for item in Branch.objects.all()}
    products = {item.sku: item for item in Product.objects.all()}
    customers_by_name: dict[str, list[Customer]] = {}
    for customer in Customer.objects.all():
        customers_by_name.setdefault(customer.name, []).append(customer)

    valid = []
    rejected = []
    seen_ids = set()
    allowed_statuses = set(Order.Status.values)

    for position, record in enumerate(records, start=1):
        identifier = _text(record.get("external_id"))
        if not identifier:
            rejected.append(_reject(f"linha {position}", "required_external_id", "ID externo obrigatório."))
            continue
        if identifier in seen_ids:
            rejected.append(_reject(identifier, "duplicate_external_id", "ID externo duplicado na fonte."))
            continue
        seen_ids.add(identifier)

        branch_name = _text(record.get("branch"))
        customer_name = _text(record.get("customer"))
        status = _text(record.get("status"))
        created_at = _datetime(record.get("created_at"))
        promised_at = _datetime(record.get("promised_at"))
        delivered_value = record.get("delivered_at")
        delivered_at = _datetime(delivered_value) if delivered_value else None
        items = record.get("items")

        error = None
        if branch_name not in branches:
            error = ("unknown_branch", f'Filial "{branch_name or "(vazia)"}" não encontrada.')
        elif len(customers_by_name.get(customer_name, [])) != 1:
            error = ("unknown_customer", f'Cliente "{customer_name or "(vazio)"}" não encontrado de forma única.')
        elif status not in allowed_statuses:
            error = ("invalid_status", f'Status "{status or "(vazio)"}" não permitido.')
        elif not created_at or not promised_at or (delivered_value and not delivered_at):
            error = ("invalid_datetime", "Datas devem usar ISO 8601 com fuso horário.")
        elif promised_at <= created_at:
            error = ("invalid_promised_at", "promised_at deve ser posterior a created_at.")
        elif delivered_at and delivered_at < created_at:
            error = ("invalid_delivered_at", "delivered_at não pode ser anterior a created_at.")
        elif status == Order.Status.DELIVERED and delivered_at is None:
            error = ("missing_delivered_at", "Pedido entregue precisa de delivered_at.")
        elif not isinstance(items, list) or not items:
            error = ("missing_items", "Pedido precisa conter ao menos um item.")

        total = Decimal("0.00")
        item_skus = set()
        if error is None:
            for item in items:
                sku = _text(item.get("sku")) if isinstance(item, dict) else ""
                price = _decimal(item.get("unit_price")) if isinstance(item, dict) else None
                quantity = item.get("quantity") if isinstance(item, dict) else None
                if sku not in products:
                    error = ("unknown_product", f'Produto "{sku or "(vazio)"}" não encontrado.')
                elif sku in item_skus:
                    error = ("duplicate_product", f'Produto "{sku}" repetido no pedido.')
                elif not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
                    error = ("invalid_quantity", f'Quantidade inválida para o produto "{sku}".')
                elif price is None or price < 0:
                    error = ("invalid_unit_price", f'Valor unitário inválido para o produto "{sku}".')
                if error:
                    break
                item_skus.add(sku)
                total += price * quantity

        declared_total = _decimal(record.get("total_amount"))
        if error is None and (declared_total is None or declared_total < 0):
            error = ("invalid_total", "Valor total do pedido deve ser um número não negativo.")
        elif error is None and declared_total.quantize(Decimal("0.01")) != total.quantize(Decimal("0.01")):
            error = ("total_mismatch", "Valor total difere da soma dos itens.")

        if error:
            rejected.append(_reject(identifier, error[0], error[1]))
        else:
            valid.append(record)
    return valid, rejected
