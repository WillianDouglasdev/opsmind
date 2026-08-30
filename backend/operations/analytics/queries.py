from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import connection
from django.db.models import Count, DecimalField, ExpressionWrapper, F, IntegerField, Q, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone

from operations.demo import DEMO_REFERENCE_DATE
from operations.models import Customer, Inventory, Order, Product, Ticket

VALID_REVENUE_STATUSES = [
    Order.Status.PENDING,
    Order.Status.PROCESSING,
    Order.Status.SHIPPED,
    Order.Status.DELIVERED,
    Order.Status.DELAYED,
]


def comparison_periods(reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    # São dois blocos de 30 dias; o fim exclusivo do anterior evita contar a fronteira duas vezes.
    current_start = timezone.make_aware(
        datetime.combine(reference_date - timedelta(days=29), time.min)
    )
    current_end = timezone.make_aware(datetime.combine(reference_date, time.max))
    previous_start = current_start - timedelta(days=30)

    return {
        "current": (current_start, current_end),
        "previous": (previous_start, current_start),
    }


def percentage_change(current, previous) -> float | None:
    # Sem base anterior, None é mais honesto do que inventar uma variação infinita.
    if previous == 0:
        return 0.0 if current == 0 else None
    return round(float((current - previous) / previous * 100), 2)


def revenue_metrics(reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    periods = comparison_periods(reference_date)
    money_field = DecimalField(max_digits=16, decimal_places=2)

    # O faturamento operacional inclui todo pedido não cancelado, sem simular regras contábeis.
    def total_for_period(start, end, inclusive_end: bool) -> Decimal:
        end_lookup = "created_at__lte" if inclusive_end else "created_at__lt"
        filters = {"created_at__gte": start, end_lookup: end}
        value = (
            Order.objects.filter(status__in=VALID_REVENUE_STATUSES, **filters).aggregate(
                value=Coalesce(Sum("total_amount"), Decimal("0.00"), output_field=money_field)
            )["value"]
        )
        return value.quantize(Decimal("0.01"))

    current = total_for_period(*periods["current"], inclusive_end=True)
    previous = total_for_period(*periods["previous"], inclusive_end=False)
    return {
        "value": current,
        "previous_value": previous,
        "change_percentage": percentage_change(current, previous),
    }


def order_metrics(reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    periods = comparison_periods(reference_date)
    current = Order.objects.filter(
        created_at__gte=periods["current"][0],
        created_at__lte=periods["current"][1],
    ).count()
    previous = Order.objects.filter(
        created_at__gte=periods["previous"][0],
        created_at__lt=periods["previous"][1],
    ).count()
    return {
        "value": current,
        "previous_value": previous,
        "change_percentage": percentage_change(current, previous),
    }


def delay_metrics(reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    periods = comparison_periods(reference_date)

    # A comparação usa a taxa, não só a contagem, para considerar o volume de cada período.
    current_orders = Order.objects.filter(
        created_at__gte=periods["current"][0],
        created_at__lte=periods["current"][1],
    )
    previous_orders = Order.objects.filter(
        created_at__gte=periods["previous"][0],
        created_at__lt=periods["previous"][1],
    )
    current_total = current_orders.count()
    previous_total = previous_orders.count()
    current_delayed = current_orders.filter(status=Order.Status.DELAYED).count()
    previous_delayed = previous_orders.filter(status=Order.Status.DELAYED).count()
    current_rate_raw = current_delayed / current_total * 100 if current_total else 0.0
    previous_rate_raw = previous_delayed / previous_total * 100 if previous_total else 0.0
    current_rate = round(current_rate_raw, 2)
    previous_rate = round(previous_rate_raw, 2)

    return {
        "value": current_delayed,
        "total_orders": current_total,
        "rate": current_rate,
        "previous_value": previous_delayed,
        "previous_total_orders": previous_total,
        "previous_rate": previous_rate,
        "change_percentage": percentage_change(current_rate_raw, previous_rate_raw),
    }


def active_ticket_metrics() -> dict:
    active_statuses = [Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS]
    active = Ticket.objects.filter(status__in=active_statuses).count()
    total = Ticket.objects.count()
    return {
        "value": active,
        "total_tickets": total,
        "active_rate": round(active / total * 100, 2) if total else 0.0,
        "definition": "Chamados com status aberto ou em andamento.",
    }


def delivery_ticket_metrics(reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    periods = comparison_periods(reference_date)
    delivery_tickets = Ticket.objects.filter(category=Ticket.Category.DELIVERY)
    current = delivery_tickets.filter(
        created_at__gte=periods["current"][0],
        created_at__lte=periods["current"][1],
    ).count()
    previous = delivery_tickets.filter(
        created_at__gte=periods["previous"][0],
        created_at__lt=periods["previous"][1],
    ).count()
    return {
        "value": current,
        "previous_value": previous,
        "change_percentage": percentage_change(current, previous),
    }


def ticket_analysis_metrics(reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    active = active_ticket_metrics()
    delivery = delivery_ticket_metrics(reference_date)
    categories = {
        row["category"]: row["value"]
        for row in Ticket.objects.values("category").annotate(value=Count("id"))
    }
    priorities = {
        row["priority"]: row["value"]
        for row in Ticket.objects.values("priority").annotate(value=Count("id"))
    }
    return {
        "total": active["total_tickets"],
        "active": active["value"],
        "active_rate": active["active_rate"],
        "categories": categories,
        "priorities": priorities,
        "delivery_recent": delivery["value"],
        "delivery_previous": delivery["previous_value"],
        "delivery_change_percentage": delivery["change_percentage"],
    }


def critical_inventory_items() -> list[dict]:
    deficit = ExpressionWrapper(
        F("minimum_quantity") - F("current_quantity"),
        output_field=IntegerField(),
    )
    return list(
        Inventory.objects.filter(current_quantity__lt=F("minimum_quantity"))
        .select_related("branch", "product")
        .annotate(deficit=deficit)
        .values(
            "product_id",
            "product__sku",
            "product__name",
            "branch_id",
            "branch__name",
            "current_quantity",
            "minimum_quantity",
            "deficit",
        )
        .order_by("product__sku", "branch__name")
    )


def recurring_strategic_customers(reference_date: date = DEMO_REFERENCE_DATE) -> list[dict]:
    current_start, current_end = comparison_periods(reference_date)["current"]
    # Duas ocorrências já indicam recorrência sem transformar um caso isolado em risco.
    return list(
        Customer.objects.filter(segment=Customer.Segment.STRATEGIC)
        .annotate(
            recent_delays=Count(
                "orders",
                filter=Q(
                    orders__created_at__gte=current_start,
                    orders__created_at__lte=current_end,
                    orders__status=Order.Status.DELAYED,
                ),
                distinct=True,
            ),
            recent_tickets=Count(
                "tickets",
                filter=Q(
                    tickets__created_at__gte=current_start,
                    tickets__created_at__lte=current_end,
                ),
                distinct=True,
            ),
        )
        .filter(Q(recent_delays__gte=2) | Q(recent_tickets__gte=2))
        .values("id", "name", "recent_delays", "recent_tickets")
        .order_by("-recent_delays", "-recent_tickets", "name")
    )


def recent_delayed_order_impact(reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    current_start, current_end = comparison_periods(reference_date)["current"]
    money_field = DecimalField(max_digits=16, decimal_places=2)
    result = Order.objects.filter(
        created_at__gte=current_start,
        created_at__lte=current_end,
        status=Order.Status.DELAYED,
    ).aggregate(
        delayed_orders=Count("id"),
        impacted_customers=Count("customer_id", distinct=True),
        affected_revenue=Coalesce(
            Sum("total_amount"),
            Decimal("0.00"),
            output_field=money_field,
        ),
    )
    result["affected_revenue"] = result["affected_revenue"].quantize(Decimal("0.01"))
    return result


def delayed_product_metrics(
    reference_date: date = DEMO_REFERENCE_DATE,
    branch_id: int | None = None,
) -> list[dict]:
    current_start, current_end = comparison_periods(reference_date)["current"]
    filters = {
        "order_items__order__created_at__gte": current_start,
        "order_items__order__created_at__lte": current_end,
        "order_items__order__status": Order.Status.DELAYED,
    }
    if branch_id is not None:
        filters["order_items__order__branch_id"] = branch_id

    return list(
        Product.objects.filter(**filters)
        .values("id", "sku", "name")
        .annotate(
            delayed_orders=Count("order_items__order_id", distinct=True),
            delayed_units=Sum("order_items__quantity"),
        )
        .order_by("-delayed_orders", "sku")
    )


def critical_inventory_signals(reference_date: date = DEMO_REFERENCE_DATE) -> list[dict]:
    critical_items = critical_inventory_items()
    if not critical_items:
        return []

    current_start, current_end = comparison_periods(reference_date)["current"]
    product_ids = {item["product_id"] for item in critical_items}
    branch_ids = {item["branch_id"] for item in critical_items}
    # A consulta mede ocorrência conjunta; ela não afirma que o estoque causou o atraso.
    related_orders = (
        Order.objects.filter(
            created_at__gte=current_start,
            created_at__lte=current_end,
            status=Order.Status.DELAYED,
            branch_id__in=branch_ids,
            items__product_id__in=product_ids,
        )
        .values("branch_id", "items__product_id")
        .annotate(delayed_orders=Count("id", distinct=True))
    )
    related_by_item = {
        (row["branch_id"], row["items__product_id"]): row["delayed_orders"]
        for row in related_orders
    }

    for item in critical_items:
        minimum = item["minimum_quantity"]
        item["percentage_below_minimum"] = (
            round(item["deficit"] / minimum * 100, 2) if minimum else 0.0
        )
        item["delayed_orders"] = related_by_item.get(
            (item["branch_id"], item["product_id"]),
            0,
        )
    return sorted(
        critical_items,
        key=lambda item: (-item["delayed_orders"], -item["deficit"], item["product__sku"]),
    )


def critical_inventory_related_order_count(
    reference_date: date = DEMO_REFERENCE_DATE,
) -> int:
    critical_items = critical_inventory_items()
    if not critical_items:
        return 0

    current_start, current_end = comparison_periods(reference_date)["current"]
    item_pairs = Q()
    for item in critical_items:
        item_pairs |= Q(branch_id=item["branch_id"], items__product_id=item["product_id"])

    # O distinct evita contar duas vezes um pedido que contenha mais de um produto crítico.
    return (
        Order.objects.filter(
            item_pairs,
            created_at__gte=current_start,
            created_at__lte=current_end,
            status=Order.Status.DELAYED,
        )
        .distinct()
        .count()
    )


def branch_delivery_ticket_count(
    branch_id: int,
    reference_date: date = DEMO_REFERENCE_DATE,
) -> int:
    current_start, current_end = comparison_periods(reference_date)["current"]
    return Ticket.objects.filter(
        category=Ticket.Category.DELIVERY,
        order__branch_id=branch_id,
        created_at__gte=current_start,
        created_at__lte=current_end,
    ).count()


def strategic_customer_impact(reference_date: date = DEMO_REFERENCE_DATE) -> dict:
    customers = recurring_strategic_customers(reference_date)
    customer_ids = [customer["id"] for customer in customers]
    current_start, current_end = comparison_periods(reference_date)["current"]
    money_field = DecimalField(max_digits=16, decimal_places=2)
    revenue = Order.objects.filter(
        customer_id__in=customer_ids,
        status__in=VALID_REVENUE_STATUSES,
        created_at__gte=current_start,
        created_at__lte=current_end,
    ).aggregate(
        value=Coalesce(
            Sum("total_amount"),
            Decimal("0.00"),
            output_field=money_field,
        )
    )["value"].quantize(Decimal("0.01"))

    return {
        "customers": customers,
        "affected_customers": len(customers),
        "revenue": revenue,
        "delayed_orders": sum(customer["recent_delays"] for customer in customers),
        "tickets": sum(customer["recent_tickets"] for customer in customers),
    }


def branch_delay_rates(reference_date: date = DEMO_REFERENCE_DATE) -> list[dict]:
    current_start, current_end = comparison_periods(reference_date)["current"]

    # O SQL explícito deixa o agrupamento por filial igual em SQLite e PostgreSQL.
    sql = """
        SELECT
            branch.id,
            branch.name,
            COUNT(orders.id) AS total_orders,
            SUM(CASE WHEN orders.status = %s THEN 1 ELSE 0 END) AS delayed_orders
        FROM operations_branch AS branch
        LEFT JOIN operations_order AS orders
            ON orders.branch_id = branch.id
            AND orders.created_at >= %s
            AND orders.created_at <= %s
        GROUP BY branch.id, branch.name
        ORDER BY delayed_orders DESC, branch.name ASC
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [Order.Status.DELAYED, current_start, current_end])
        rows = cursor.fetchall()

    return [
        {
            "branch_id": branch_id,
            "branch_name": name,
            "total_orders": total,
            "delayed_orders": delayed or 0,
            "delay_rate": round((delayed or 0) / total * 100, 2) if total else 0.0,
        }
        for branch_id, name, total, delayed in rows
    ]


def monthly_on_time_delivery(reference_date: date = DEMO_REFERENCE_DATE) -> list[dict]:
    start_month_index = reference_date.year * 12 + reference_date.month - 1 - 5
    start_year, zero_based_month = divmod(start_month_index, 12)
    start_month = date(start_year, zero_based_month + 1, 1)
    range_start = timezone.make_aware(datetime.combine(start_month, time.min))
    range_end = timezone.make_aware(datetime.combine(reference_date, time.max))

    # Só entram pedidos cujo prazo já venceu; pedidos ainda dentro do prazo distorceriam a taxa.
    rows = (
        Order.objects.filter(
            created_at__gte=range_start,
            created_at__lte=range_end,
            promised_at__lte=range_end,
            status__in=[Order.Status.DELIVERED, Order.Status.DELAYED],
        )
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            total_orders=Count("id"),
            on_time_orders=Count(
                "id",
                filter=Q(delivered_at__isnull=False, delivered_at__lte=F("promised_at")),
            ),
        )
        .order_by("month")
    )
    values_by_month = {
        (row["month"].year, row["month"].month): row
        for row in rows
    }
    month_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    series = []

    for offset in range(6):
        month_index = start_month_index + offset
        year, month_zero_based = divmod(month_index, 12)
        month = month_zero_based + 1
        row = values_by_month.get((year, month), {})
        total = row.get("total_orders", 0)
        on_time = row.get("on_time_orders", 0)
        series.append(
            {
                "month": f"{year:04d}-{month:02d}",
                "label": month_labels[month - 1],
                "value": round(on_time / total * 100, 2) if total else 0.0,
                "total_orders": total,
            }
        )

    return series
