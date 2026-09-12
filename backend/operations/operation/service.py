"""Agregações de drill-down usadas somente pelas APIs de leitura da Operação."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.paginator import EmptyPage, Paginator
from django.db.models import Count, DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from operations.analytics.dashboard import calculate_operational_health
from operations.analytics.queries import VALID_REVENUE_STATUSES, percentage_change
from operations.demo import DEMO_REFERENCE_DATE
from operations.models import Branch, Customer, Inventory, Order, Ticket

ALLOWED_PERIOD_DAYS = (7, 30, 90)
ACTIVE_TICKET_STATUSES = (Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS)
MONEY_FIELD = DecimalField(max_digits=16, decimal_places=2)
DELAY_DEFINITION = {
    "metric_key": "order_delay_rate",
    "entity": "orders",
    "field": "status",
    "rule": "status = delayed",
    "pipeline_key": "orders",
}


class OperationNotFound(Exception):
    pass


def period_bounds(days: int, reference_date: date = DEMO_REFERENCE_DATE) -> tuple[datetime, datetime]:
    """Retorna início inclusivo e fim exclusivo no fuso configurado pelo Django."""
    if days not in ALLOWED_PERIOD_DAYS:
        raise ValueError("Período operacional não suportado.")
    start_date = reference_date - timedelta(days=days - 1)
    start = timezone.make_aware(datetime.combine(start_date, time.min))
    end = timezone.make_aware(datetime.combine(reference_date + timedelta(days=1), time.min))
    return start, end


def _period_payload(days: int, reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    start, end = period_bounds(days, reference_date)
    return {
        "days": days,
        "start_date": start.date(),
        "end_date": reference_date,
        "reference_date": reference_date,
    }


def _rate(part: int, total: int) -> float:
    return round(part / total * 100, 2) if total else 0.0


def _branch_rows(days: int, reference_date: date = DEMO_REFERENCE_DATE) -> tuple[list[dict], dict]:
    start, end = period_bounds(days, reference_date)
    previous_start = start - timedelta(days=days)
    current_filter = Q(created_at__gte=start, created_at__lt=end)

    current_orders = {
        row["branch_id"]: row
        for row in Order.objects.filter(current_filter)
        .values("branch_id")
        .annotate(
            orders=Count("id"),
            delayed_orders=Count("id", filter=Q(status=Order.Status.DELAYED)),
            revenue=Coalesce(
                Sum("total_amount", filter=Q(status__in=VALID_REVENUE_STATUSES)),
                Decimal("0.00"),
                output_field=MONEY_FIELD,
            ),
            customers=Count("customer_id", distinct=True),
            impacted_customers=Count(
                "customer_id", filter=Q(status=Order.Status.DELAYED), distinct=True,
            ),
            strategic_customers=Count(
                "customer_id",
                filter=Q(customer__segment=Customer.Segment.STRATEGIC),
                distinct=True,
            ),
            impacted_strategic_customers=Count(
                "customer_id",
                filter=Q(
                    status=Order.Status.DELAYED,
                    customer__segment=Customer.Segment.STRATEGIC,
                ),
                distinct=True,
            ),
        )
    }
    previous_orders = {
        row["branch_id"]: row
        for row in Order.objects.filter(created_at__gte=previous_start, created_at__lt=start)
        .values("branch_id")
        .annotate(
            orders=Count("id"),
            delayed_orders=Count("id", filter=Q(status=Order.Status.DELAYED)),
        )
    }
    tickets = {
        row["order__branch_id"]: row
        for row in Ticket.objects.filter(order__isnull=False)
        .values("order__branch_id")
        .annotate(
            total_tickets=Count("id"),
            active_tickets=Count("id", filter=Q(status__in=ACTIVE_TICKET_STATUSES)),
        )
    }
    inventory = {
        row["branch_id"]: row
        for row in Inventory.objects.values("branch_id").annotate(
            inventory_items=Count("id"),
            critical_inventory=Count("id", filter=Q(current_quantity__lt=F("minimum_quantity"))),
        )
    }

    raw_rows = []
    for branch in Branch.objects.all():
        current = current_orders.get(branch.pk, {})
        previous = previous_orders.get(branch.pk, {})
        ticket = tickets.get(branch.pk, {})
        stock = inventory.get(branch.pk, {})
        orders = current.get("orders", 0)
        delayed = current.get("delayed_orders", 0)
        previous_total = previous.get("orders", 0)
        previous_delayed = previous.get("delayed_orders", 0)
        raw_rows.append({
            "id": branch.pk,
            "name": branch.name,
            "city": branch.city,
            "state": branch.state,
            "orders": orders,
            "delayed_orders": delayed,
            "delay_rate": _rate(delayed, orders),
            "previous_delay_rate": _rate(previous_delayed, previous_total),
            "revenue": current.get("revenue", Decimal("0.00")),
            "customers": current.get("customers", 0),
            "impacted_customers": current.get("impacted_customers", 0),
            "strategic_customers": current.get("strategic_customers", 0),
            "impacted_strategic_customers": current.get("impacted_strategic_customers", 0),
            "active_tickets": ticket.get("active_tickets", 0),
            "total_tickets": ticket.get("total_tickets", 0),
            "critical_inventory": stock.get("critical_inventory", 0),
            "inventory_items": stock.get("inventory_items", 0),
        })

    organization_orders = sum(row["orders"] for row in raw_rows)
    organization_delays = sum(row["delayed_orders"] for row in raw_rows)
    organization_delay_rate = _rate(organization_delays, organization_orders)
    rows = []
    for row in raw_rows:
        if row["orders"]:
            previous_rate_raw = row["previous_delay_rate"]
            growth = percentage_change(row["delay_rate"], previous_rate_raw) or 0.0
            health = calculate_operational_health({
                "delay_rate": row["delay_rate"],
                "delay_growth": growth,
                "critical_inventory_rate": _rate(row["critical_inventory"], row["inventory_items"]),
                "active_ticket_rate": _rate(row["active_tickets"], row["total_tickets"]),
                "strategic_customer_rate": _rate(
                    row["impacted_strategic_customers"], row["strategic_customers"],
                ),
                "worst_branch_gap": max(0.0, row["delay_rate"] - organization_delay_rate),
            })
            row["health"] = {key: health[key] for key in ("score", "status")}
        else:
            # Sem pedidos no período não há base para classificar a saúde da unidade.
            row["health"] = None
        rows.append(row)

    branch_count = len(rows)
    delay_rows = [row for row in rows if row["orders"]]
    health_rows = [row for row in rows if row["health"]]
    average = {
        "orders": round(organization_orders / branch_count, 2) if branch_count else None,
        "delay_rate": (
            round(sum(row["delay_rate"] for row in delay_rows) / len(delay_rows), 2)
            if delay_rows else None
        ),
        "revenue": (
            (sum((row["revenue"] for row in rows), Decimal("0.00")) / branch_count).quantize(Decimal("0.01"))
            if branch_count else None
        ),
        "active_tickets": (
            round(sum(row["active_tickets"] for row in rows) / branch_count, 2)
            if branch_count else None
        ),
        "health_score": (
            round(sum(row["health"]["score"] for row in health_rows) / len(health_rows), 2)
            if health_rows else None
        ),
    }
    return rows, average


def _critical_products(limit: int = 4) -> list[dict]:
    rows = (
        Inventory.objects.filter(current_quantity__lt=F("minimum_quantity"))
        .values("product__sku", "product__name")
        .annotate(
            affected_branches=Count("branch_id", distinct=True),
            available=Sum("current_quantity"),
            minimum=Sum("minimum_quantity"),
        )
        .order_by("available", "product__sku")[:limit]
    )
    return [{
        "sku": row["product__sku"],
        "name": row["product__name"],
        "affected_branches": row["affected_branches"],
        "available": row["available"],
        "minimum": row["minimum"],
        "deficit": row["minimum"] - row["available"],
    } for row in rows]


def build_operation_overview(days: int = 30) -> dict:
    start, end = period_bounds(days)
    branches, average = _branch_rows(days)
    orders = sum(row["orders"] for row in branches)
    delayed = sum(row["delayed_orders"] for row in branches)
    current_orders = Order.objects.filter(created_at__gte=start, created_at__lt=end)
    worst_branch = max(
        (row for row in branches if row["orders"]),
        key=lambda row: (row["delay_rate"], row["delayed_orders"]),
        default=None,
    )
    return {
        "period": _period_payload(days),
        "metrics": {
            "orders": orders,
            "delayed_orders": delayed,
            "delay_rate": _rate(delayed, orders),
            "revenue": sum((row["revenue"] for row in branches), Decimal("0.00")),
            "customers": current_orders.values("customer_id").distinct().count(),
            "active_tickets": Ticket.objects.filter(status__in=ACTIVE_TICKET_STATUSES).count(),
            "critical_inventory": Inventory.objects.filter(
                current_quantity__lt=F("minimum_quantity")
            ).count(),
        },
        "branch_average": average,
        "branches": branches,
        "attention": {
            "worst_branch": worst_branch,
            "critical_products": _critical_products(),
            "strategic_customers_impacted": current_orders.filter(
                status=Order.Status.DELAYED,
                customer__segment=Customer.Segment.STRATEGIC,
            ).values("customer_id").distinct().count(),
        },
        "metric_definition": DELAY_DEFINITION,
    }


def _branch_trend(branch_id: int, days: int) -> list[dict]:
    start, end = period_bounds(days)
    rows = {
        row["day"]: row
        for row in Order.objects.filter(
            branch_id=branch_id, created_at__gte=start, created_at__lt=end,
        )
        .annotate(day=TruncDate("created_at", tzinfo=timezone.get_current_timezone()))
        .values("day")
        .annotate(
            orders=Count("id"),
            delayed_orders=Count("id", filter=Q(status=Order.Status.DELAYED)),
            revenue=Coalesce(
                Sum("total_amount", filter=Q(status__in=VALID_REVENUE_STATUSES)),
                Decimal("0.00"), output_field=MONEY_FIELD,
            ),
        )
        .order_by("day")
    }
    return [{
        "date": day,
        "orders": rows.get(day, {}).get("orders", 0),
        "delayed_orders": rows.get(day, {}).get("delayed_orders", 0),
        "delay_rate": _rate(
            rows.get(day, {}).get("delayed_orders", 0),
            rows.get(day, {}).get("orders", 0),
        ),
        "revenue": rows.get(day, {}).get("revenue", Decimal("0.00")),
    } for day in (start.date() + timedelta(days=offset) for offset in range(days))]


def build_branch_detail(branch_id: int, days: int = 30) -> dict:
    branches, average = _branch_rows(days)
    branch = next((row for row in branches if row["id"] == branch_id), None)
    if branch is None:
        raise OperationNotFound("Filial não encontrada.")

    comparisons = [
        ("delay_rate", "Atrasos", "percentage", branch["delay_rate"], average["delay_rate"]),
        ("orders", "Pedidos", "count", branch["orders"], average["orders"]),
        ("revenue", "Receita", "currency", branch["revenue"], average["revenue"]),
        ("active_tickets", "Chamados ativos", "count", branch["active_tickets"], average["active_tickets"]),
        ("health_score", "Saúde operacional", "score", branch["health"]["score"] if branch["health"] else None, average["health_score"]),
    ]
    return {
        "period": _period_payload(days),
        "branch": {key: branch[key] for key in ("id", "name", "city", "state")},
        "metrics": branch,
        "comparison_scope": (
            "Média aritmética das filiais; taxas e saúde excluem unidades sem pedidos. "
            "Chamados e estoque representam o snapshot atual."
        ),
        "comparisons": [{
            "key": key,
            "label": label,
            "unit": unit,
            "branch_value": value,
            "average_value": average_value,
            "difference": value - average_value if value is not None and average_value is not None else None,
        } for key, label, unit, value, average_value in comparisons],
        "trend": _branch_trend(branch_id, days),
        "metric_definition": DELAY_DEFINITION,
    }


def build_delay_overview(days: int = 30) -> dict:
    start, end = period_bounds(days)
    branches, _average = _branch_rows(days)
    total_orders = sum(row["orders"] for row in branches)
    total_delayed = sum(row["delayed_orders"] for row in branches)
    ranked = sorted(
        branches,
        key=lambda row: (-row["delayed_orders"], -row["delay_rate"], row["name"]),
    )
    return {
        "period": _period_payload(days),
        "metrics": {
            "orders": total_orders,
            "delayed_orders": total_delayed,
            "delay_rate": _rate(total_delayed, total_orders),
            "impacted_customers": Order.objects.filter(
                created_at__gte=start,
                created_at__lt=end,
                status=Order.Status.DELAYED,
            ).values("customer_id").distinct().count(),
        },
        "branches": [{
            **row,
            "contribution_percentage": _rate(row["delayed_orders"], total_delayed),
        } for row in ranked],
        "metric_definition": DELAY_DEFINITION,
    }


def _delivery_state(order: Order, reference_end: datetime) -> tuple[str, str]:
    if order.status == Order.Status.DELAYED:
        return "late", "Atrasado"
    if order.status == Order.Status.CANCELLED:
        return "cancelled", "Cancelado"
    if order.delivered_at:
        if order.delivered_at <= order.promised_at:
            return "delivered_on_time", "Entregue no prazo"
        return "delivered_after_promise", "Entregue após o prazo"
    if order.promised_at < reference_end:
        return "past_promise", "Prazo vencido no status atual"
    return "in_progress", "Em andamento"


def list_operation_orders(
    *, days: int = 30, branch_id: int | None = None, status: str = "",
    delivery: str = "all", page: int = 1, page_size: int = 15,
) -> dict:
    start, end = period_bounds(days)
    queryset = Order.objects.filter(created_at__gte=start, created_at__lt=end)
    if branch_id is not None:
        queryset = queryset.filter(branch_id=branch_id)
    if status:
        queryset = queryset.filter(status=status)
    if delivery == "late":
        # O filtro segue o mesmo contrato do KPI e não reclassifica pedidos pelas datas.
        queryset = queryset.filter(status=Order.Status.DELAYED)
    queryset = queryset.select_related("branch", "customer").order_by("-created_at", "-id")
    paginator = Paginator(queryset, page_size)
    try:
        page_object = paginator.page(page)
    except EmptyPage as error:
        raise ValueError("Página fora do intervalo disponível.") from error

    results = []
    for order in page_object.object_list:
        state, state_label = _delivery_state(order, end)
        results.append({
            "id": order.pk,
            "identifier": order.external_id or f"#{order.pk}",
            "customer": {"id": order.customer_id, "name": order.customer.name},
            "branch": {"id": order.branch_id, "name": order.branch.name},
            "created_at": order.created_at,
            "promised_at": order.promised_at,
            "total_amount": order.total_amount,
            "status": order.status,
            "status_label": order.get_status_display(),
            "delivery_state": state,
            "delivery_state_label": state_label,
        })
    return {
        "period": _period_payload(days),
        "count": paginator.count,
        "page": page_object.number,
        "page_size": page_size,
        "total_pages": paginator.num_pages,
        "results": results,
    }
