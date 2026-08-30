from django.urls import path

from operations.views import dashboard_changes, dashboard_summary, dashboard_trends

urlpatterns = [
    path("summary/", dashboard_summary, name="dashboard-summary"),
    path("trends/", dashboard_trends, name="dashboard-trends"),
    path("changes/", dashboard_changes, name="dashboard-changes"),
]

