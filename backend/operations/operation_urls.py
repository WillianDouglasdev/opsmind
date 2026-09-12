from django.urls import path

from operations.operation_views import (
    operation_branch_detail,
    operation_delays,
    operation_orders,
    operation_overview,
)

urlpatterns = [
    path("overview/", operation_overview, name="operation-overview"),
    path("delays/", operation_delays, name="operation-delays"),
    path("branches/<int:branch_id>/", operation_branch_detail, name="operation-branch-detail"),
    path("orders/", operation_orders, name="operation-orders"),
]
