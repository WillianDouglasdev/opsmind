from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/dashboard/", include("operations.urls")),
    path("api/alerts/", include("operations.alert_urls")),
    path("api/actions/", include("operations.action_urls")),
    path("api/assistant/", include("operations.assistant_urls")),
    path("api/data/pipelines/", include("operations.pipeline_urls")),
    path("api/operation/", include("operations.operation_urls")),
    path("api/investigations/", include("operations.investigation_urls")),
    path("api/", include("core.urls")),
]
