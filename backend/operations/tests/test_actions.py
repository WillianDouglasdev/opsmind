import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

import operations.actions.recommendations as recommendations_module
from operations.actions import (
    DuplicateActionError,
    RecommendationNotFound,
    build_recommendations,
    create_action_item,
    list_action_items,
    update_action_status,
)
from operations.alerts import AlertNotFound, build_investigation, get_active_alerts
from operations.models import ActionItem

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def full_demo(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("seed_demo", reset=True, verbosity=0)
    yield
    with django_db_blocker.unblock():
        call_command("flush", interactive=False, verbosity=0)


@pytest.fixture(autouse=True)
def clean_action_items(full_demo):
    ActionItem.objects.all().delete()


def test_every_active_alert_has_stable_recommendations() -> None:
    alerts = get_active_alerts()

    assert {alert["type"] for alert in alerts} == {
        "DELIVERY_DELAY_INCREASE",
        "BRANCH_PERFORMANCE",
        "INVENTORY_RISK",
        "STRATEGIC_CUSTOMER_RISK",
    }
    for alert in alerts:
        recommendations = build_recommendations(alert["key"])
        keys = [item["recommendation_key"] for item in recommendations]
        assert len(recommendations) == 3
        assert len(keys) == len(set(keys))
        assert all(item["reason"] for item in recommendations)
        assert all(item["alert_key"] == alert["key"] for item in recommendations)


def test_branch_recommendations_use_current_investigation_data() -> None:
    alert = next(
        alert for alert in get_active_alerts() if alert["type"] == "BRANCH_PERFORMANCE"
    )
    investigation = build_investigation(alert["key"])
    branch_name = investigation["_recommendation_context"]["branch"]["branch_name"]
    recommendations = build_recommendations(alert["key"])

    assert branch_name == "Contagem"
    assert any(branch_name in item["title"] for item in recommendations)
    assert any("p.p." in item["reason"] for item in recommendations)


def test_inventory_recommendations_use_current_product_skus() -> None:
    investigation = build_investigation("inventory-risk")
    expected_skus = {
        item["product__sku"]
        for item in investigation["_recommendation_context"]["items"]
    }
    recommendation = next(
        item
        for item in build_recommendations("inventory-risk")
        if item["recommendation_key"] == "review-critical-inventory"
    )

    assert expected_skus
    assert all(sku in recommendation["title"] for sku in expected_skus)


def test_recommendations_do_not_parse_investigation_text(monkeypatch) -> None:
    original_builder = recommendations_module.build_investigation

    def build_with_changed_presentation(alert_key: str) -> dict:
        investigation = original_builder(alert_key)
        investigation["context"] = "Texto de apresentação alterado."
        for metric in investigation["impact"]:
            metric["label"] = "Rótulo alterado"
        for section in investigation["related_signals"] + investigation["evidence"]:
            section["title"] = "Título alterado"
            section["description"] = "Descrição alterada sem dados operacionais."
            for metric in section["metrics"]:
                metric["label"] = "Rótulo alterado"
        return investigation

    monkeypatch.setattr(
        recommendations_module,
        "build_investigation",
        build_with_changed_presentation,
    )

    delivery = build_recommendations("delivery-delay-increase")
    inventory = build_recommendations("inventory-risk")

    assert any("filial Contagem" in item["title"] for item in delivery)
    assert any(
        "P018" in item["title"] and "P027" in item["title"]
        for item in inventory
    )
    assert any("Contagem" in item["reason"] for item in inventory)


def test_create_action_uses_official_recommendation_content() -> None:
    recommendation = build_recommendations("delivery-delay-increase")[0]
    action = create_action_item(
        "delivery-delay-increase",
        recommendation["recommendation_key"],
    )

    assert action.title == recommendation["title"]
    assert action.description == recommendation["description"]
    assert action.priority == recommendation["priority"]
    assert action.status == ActionItem.Status.PENDING
    assert action.source_alert_type == "DELIVERY_DELAY_INCREASE"


def test_invalid_alert_and_recommendation_are_rejected() -> None:
    with pytest.raises(AlertNotFound):
        create_action_item("alerta-inexistente", "review-worst-branch")

    with pytest.raises(RecommendationNotFound):
        create_action_item("delivery-delay-increase", "recomendacao-inexistente")


def test_open_duplicate_is_rejected() -> None:
    action = create_action_item("delivery-delay-increase", "review-worst-branch")

    with pytest.raises(DuplicateActionError) as error:
        create_action_item("delivery-delay-increase", "review-worst-branch")

    assert error.value.action.pk == action.pk
    assert ActionItem.objects.count() == 1


def test_completion_reopening_and_repeating_completed_action() -> None:
    action = create_action_item("delivery-delay-increase", "review-worst-branch")

    update_action_status(action, ActionItem.Status.COMPLETED)
    assert action.completed_at is not None

    update_action_status(action, ActionItem.Status.IN_PROGRESS)
    assert action.completed_at is None

    update_action_status(action, ActionItem.Status.COMPLETED)
    repeated = create_action_item("delivery-delay-increase", "review-worst-branch")
    assert repeated.pk != action.pk


def test_action_list_orders_open_items_before_completed() -> None:
    pending = create_action_item("delivery-delay-increase", "monitor-delivery-tickets")
    in_progress = create_action_item("inventory-risk", "review-critical-inventory")
    completed = create_action_item("strategic-customer-risk", "review-strategic-customers")
    update_action_status(in_progress, ActionItem.Status.IN_PROGRESS)
    update_action_status(completed, ActionItem.Status.COMPLETED)

    action_ids = list(list_action_items().values_list("id", flat=True))

    assert action_ids.index(pending.id) < action_ids.index(in_progress.id)
    assert action_ids[-1] == completed.id


def test_recommendations_and_actions_endpoints() -> None:
    client = APIClient()
    recommendations = client.get(
        "/api/alerts/delivery-delay-increase/recommendations/"
    )
    recommendation_key = recommendations.json()[0]["recommendation_key"]
    created = client.post(
        "/api/actions/",
        {
            "alert_key": "delivery-delay-increase",
            "recommendation_key": recommendation_key,
        },
        format="json",
    )
    duplicate = client.post(
        "/api/actions/",
        {
            "alert_key": "delivery-delay-increase",
            "recommendation_key": recommendation_key,
        },
        format="json",
    )
    listed = client.get("/api/actions/")
    patched = client.patch(
        f"/api/actions/{created.json()['id']}/",
        {"status": "completed"},
        format="json",
    )

    assert recommendations.status_code == 200
    assert recommendations.json()[0]["is_added"] is False
    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["action"]["id"] == created.json()["id"]
    assert listed.status_code == 200
    assert patched.status_code == 200
    assert patched.json()["completed_at"] is not None


def test_endpoints_reject_invalid_or_extra_fields() -> None:
    client = APIClient()
    invalid_alert = client.post(
        "/api/actions/",
        {"alert_key": "inexistente", "recommendation_key": "review-worst-branch"},
        format="json",
    )
    invalid_recommendation = client.post(
        "/api/actions/",
        {
            "alert_key": "delivery-delay-increase",
            "recommendation_key": "inexistente",
        },
        format="json",
    )
    extra_create = client.post(
        "/api/actions/",
        {
            "alert_key": "delivery-delay-increase",
            "recommendation_key": "review-worst-branch",
            "title": "Título adulterado",
        },
        format="json",
    )
    action = create_action_item("delivery-delay-increase", "review-worst-branch")
    extra_patch = client.patch(
        f"/api/actions/{action.id}/",
        {"status": "completed", "priority": "low"},
        format="json",
    )
    invalid_status = client.patch(
        f"/api/actions/{action.id}/",
        {"status": "cancelled"},
        format="json",
    )

    assert invalid_alert.status_code == 404
    assert invalid_recommendation.status_code == 404
    assert extra_create.status_code == 400
    assert extra_patch.status_code == 400
    assert invalid_status.status_code == 400
