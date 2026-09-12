from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from operations.models import Branch, Customer, Product


@dataclass(frozen=True)
class RejectedRecord:
    record_identifier: str
    code: str
    message: str


@dataclass(frozen=True)
class CleanOrderItem:
    product: Product
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class CleanOrder:
    external_id: str
    customer: Customer
    branch: Branch
    created_at: datetime
    promised_at: datetime
    delivered_at: datetime | None
    status: str
    total_amount: Decimal
    items: tuple[CleanOrderItem, ...]
