from decimal import Decimal

from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Branch(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]
        verbose_name = "Filial"
        verbose_name_plural = "Filiais"

    def __str__(self) -> str:
        return self.name


class Customer(models.Model):
    class Segment(models.TextChoices):
        RETAIL = "retail", "Varejo"
        SMALL_BUSINESS = "small_business", "Pequena empresa"
        CORPORATE = "corporate", "Corporativo"
        STRATEGIC = "strategic", "Estratégico"

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        INACTIVE = "inactive", "Inativo"

    name = models.CharField(max_length=150)
    segment = models.CharField(max_length=20, choices=Segment.choices)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["segment", "status"], name="ops_customer_seg_status_idx")]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class Category(models.TextChoices):
        ELECTRONICS = "electronics", "Eletrônicos"
        OFFICE = "office", "Escritório"
        SUPPLIES = "supplies", "Suprimentos"
        EQUIPMENT = "equipment", "Equipamentos"
        ACCESSORIES = "accessories", "Acessórios"

    sku = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=Category.choices)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["sku"]
        constraints = [
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="product_unit_price_non_negative",
            )
        ]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"


class Inventory(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )
    # A demo guarda o retrato atual do estoque, sem simular um histórico de movimentações.
    current_quantity = models.PositiveIntegerField()
    minimum_quantity = models.PositiveIntegerField()
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["branch__name", "product__sku"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "product"],
                name="unique_inventory_branch_product",
            ),
            models.CheckConstraint(
                condition=Q(current_quantity__gte=0),
                name="inventory_current_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(minimum_quantity__gte=0),
                name="inventory_minimum_non_negative",
            ),
        ]
        verbose_name = "Estoque"
        verbose_name_plural = "Estoques"

    def __str__(self) -> str:
        return f"{self.branch} · {self.product.sku}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSING = "processing", "Em processamento"
        SHIPPED = "shipped", "Enviado"
        DELIVERED = "delivered", "Entregue"
        DELAYED = "delayed", "Atrasado"
        CANCELLED = "cancelled", "Cancelado"

    # Pedidos preservam cliente e filial porque formam o histórico operacional da empresa.
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    created_at = models.DateTimeField(default=timezone.now)
    promised_at = models.DateTimeField()
    delivered_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices)
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"], name="ops_order_created_idx"),
            models.Index(fields=["status", "-created_at"], name="ops_order_status_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="order_total_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(promised_at__gt=F("created_at")),
                name="order_promise_after_creation",
            ),
            models.CheckConstraint(
                condition=Q(delivered_at__isnull=True) | Q(delivered_at__gte=F("created_at")),
                name="order_delivery_after_creation",
            ),
        ]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self) -> str:
        return f"Pedido #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()
    # O preço fica no item para uma mudança futura no produto não reescrever pedidos antigos.
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="order_item_price_non_negative",
            ),
        ]
        verbose_name = "Item do pedido"
        verbose_name_plural = "Itens dos pedidos"

    def __str__(self) -> str:
        return f"{self.product.sku} × {self.quantity}"


class Ticket(models.Model):
    class Category(models.TextChoices):
        DELIVERY = "delivery", "Entrega"
        PRODUCT = "product", "Produto"
        BILLING = "billing", "Faturamento"
        SERVICE = "service", "Atendimento"
        OTHER = "other", "Outro"

    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"
        CRITICAL = "critical", "Crítica"

    class Status(models.TextChoices):
        OPEN = "open", "Aberto"
        IN_PROGRESS = "in_progress", "Em andamento"
        RESOLVED = "resolved", "Resolvido"

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="tickets",
    )
    # Um chamado continua útil mesmo se perder a referência opcional ao pedido.
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        related_name="tickets",
        null=True,
        blank=True,
    )
    category = models.CharField(max_length=12, choices=Category.choices)
    priority = models.CharField(max_length=12, choices=Priority.choices)
    description = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices)
    created_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="ops_ticket_status_created_idx"),
            models.Index(fields=["category", "-created_at"], name="ops_ticket_cat_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(closed_at__isnull=True) | Q(closed_at__gte=F("created_at")),
                name="ticket_close_after_creation",
            )
        ]
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"

    def __str__(self) -> str:
        return f"Chamado #{self.pk} · {self.get_category_display()}"


class ActionItem(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"
        CRITICAL = "critical", "Crítica"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        IN_PROGRESS = "in_progress", "Em andamento"
        COMPLETED = "completed", "Concluída"

    # Alertas são calculados em tempo real, então a ação guarda chaves em vez de uma ForeignKey.
    recommendation_key = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField()
    source_alert_key = models.CharField(max_length=120)
    source_alert_type = models.CharField(max_length=64)
    priority = models.CharField(max_length=12, choices=Priority.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Depois de concluída, a mesma recomendação pode voltar se o problema reaparecer.
            models.UniqueConstraint(
                fields=["source_alert_key", "recommendation_key"],
                condition=Q(status__in=["pending", "in_progress"]),
                name="unique_open_action_recommendation",
            )
        ]
        verbose_name = "Item de ação"
        verbose_name_plural = "Itens de ação"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        # Ao reabrir uma ação, ela volta ao trabalho ativo e deixa de ter data de conclusão.
        if self.status == self.Status.COMPLETED and self.completed_at is None:
            self.completed_at = timezone.now()
        elif self.status != self.Status.COMPLETED:
            self.completed_at = None

        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "status" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"completed_at"}
        super().save(*args, **kwargs)
