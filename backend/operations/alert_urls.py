from django.urls import path

from operations.views import alert_investigation, alert_list, alert_recommendations

urlpatterns = [
    path("", alert_list, name="alert-list"),
    path("<slug:alert_key>/investigation/", alert_investigation, name="alert-investigation"),
    path("<slug:alert_key>/recommendations/", alert_recommendations, name="alert-recommendations"),
]
