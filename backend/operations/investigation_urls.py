from django.urls import path

from operations.investigation_views import (
    delivery_delay_investigation,
    investigation_collection,
)

urlpatterns = [
    path("", investigation_collection, name="investigation-collection"),
    path(
        "delivery-delays/",
        delivery_delay_investigation,
        name="delivery-delay-investigation",
    ),
]
