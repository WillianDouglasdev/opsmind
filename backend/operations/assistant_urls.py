from django.urls import path

from operations.views import assistant_executive_summary, assistant_query

urlpatterns = [
    path("query/", assistant_query, name="assistant-query"),
    path(
        "executive-summary/",
        assistant_executive_summary,
        name="assistant-executive-summary",
    ),
]
