from django.urls import path

from operations.views import action_collection, action_detail

urlpatterns = [
    path("", action_collection, name="action-collection"),
    path("<int:action_id>/", action_detail, name="action-detail"),
]
