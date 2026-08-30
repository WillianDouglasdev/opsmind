from django.contrib import admin

from operations.models import (
    ActionItem,
    Branch,
    Customer,
    Inventory,
    Order,
    OrderItem,
    Product,
    Ticket,
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "created_at")
    search_fields = ("name", "city")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "segment", "city", "state", "status", "created_at")
    list_filter = ("segment", "status", "state")
    search_fields = ("name", "city")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "unit_price", "created_at")
    list_filter = ("category",)
    search_fields = ("sku", "name")


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "branch",
        "product",
        "current_quantity",
        "minimum_quantity",
        "updated_at",
    )
    list_filter = ("branch",)
    search_fields = ("product__sku", "product__name", "branch__name")
    list_select_related = ("branch", "product")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "branch",
        "status",
        "created_at",
        "promised_at",
        "total_amount",
    )
    list_filter = ("status", "branch", "created_at")
    search_fields = ("=id", "customer__name")
    list_select_related = ("customer", "branch")
    date_hierarchy = "created_at"
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "unit_price")
    search_fields = ("=order__id", "product__sku", "product__name")
    list_select_related = ("order", "product")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "order",
        "category",
        "priority",
        "status",
        "created_at",
    )
    list_filter = ("category", "priority", "status", "created_at")
    search_fields = ("=id", "customer__name", "description")
    list_select_related = ("customer", "order")
    date_hierarchy = "created_at"


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "priority",
        "status",
        "source_alert_type",
        "created_at",
        "completed_at",
    )
    list_filter = ("priority", "status", "source_alert_type")
    search_fields = ("title",)
    date_hierarchy = "created_at"


admin.site.site_header = "OpsMind — Administração"
admin.site.site_title = "OpsMind Admin"
admin.site.index_title = "Dados operacionais da demo"
