from django.urls import path

from operations.views import pipeline_collection, pipeline_detail, pipeline_run_detail

urlpatterns = [
    path("", pipeline_collection, name="pipeline-collection"),
    path("<str:pipeline_key>/", pipeline_detail, name="pipeline-detail"),
    path("<str:pipeline_key>/runs/<int:run_id>/", pipeline_run_detail, name="pipeline-run-detail"),
]
