import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_endpoint_returns_ok(api_client: APIClient) -> None:
    response = api_client.get(
        reverse("health"),
        HTTP_ORIGIN="http://localhost:5173",
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "opsmind-api",
    }
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()
