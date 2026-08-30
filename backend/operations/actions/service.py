from django.db import IntegrityError, transaction
from django.db.models import Case, IntegerField, Value, When

from operations.actions.recommendations import build_recommendations
from operations.models import ActionItem


class RecommendationNotFound(Exception):
    pass


class DuplicateActionError(Exception):
    def __init__(self, action: ActionItem):
        self.action = action
        super().__init__("A recomendação já possui uma ação aberta.")


def get_alert_recommendations(alert_key: str) -> list[dict]:
    recommendations = build_recommendations(alert_key)
    open_keys = set(
        ActionItem.objects.filter(
            source_alert_key=alert_key,
            status__in=[ActionItem.Status.PENDING, ActionItem.Status.IN_PROGRESS],
        ).values_list("recommendation_key", flat=True)
    )
    # A interface marca somente ações abertas; uma ação concluída pode voltar a ser sugerida.
    return [
        {
            **recommendation,
            "is_added": recommendation["recommendation_key"] in open_keys,
        }
        for recommendation in recommendations
    ]


def create_action_item(alert_key: str, recommendation_key: str) -> ActionItem:
    # A recomendação é recalculada para não confiar em textos enviados pelo frontend.
    recommendation = next(
        (
            item
            for item in build_recommendations(alert_key)
            if item["recommendation_key"] == recommendation_key
        ),
        None,
    )
    if recommendation is None:
        raise RecommendationNotFound(recommendation_key)

    open_statuses = [ActionItem.Status.PENDING, ActionItem.Status.IN_PROGRESS]
    try:
        with transaction.atomic():
            existing = (
                ActionItem.objects.select_for_update()
                .filter(
                    source_alert_key=alert_key,
                    recommendation_key=recommendation_key,
                    status__in=open_statuses,
                )
                .first()
            )
            if existing:
                raise DuplicateActionError(existing)
            # Título, descrição e prioridade sempre vêm da recomendação oficial recalculada.
            return ActionItem.objects.create(
                recommendation_key=recommendation["recommendation_key"],
                title=recommendation["title"],
                description=recommendation["description"],
                source_alert_key=recommendation["alert_key"],
                source_alert_type=recommendation["alert_type"],
                priority=recommendation["priority"],
            )
    except IntegrityError:
        existing = ActionItem.objects.get(
            source_alert_key=alert_key,
            recommendation_key=recommendation_key,
            status__in=open_statuses,
        )
        raise DuplicateActionError(existing) from None


def list_action_items():
    # Itens ativos aparecem primeiro e, dentro do mesmo status, vence a maior prioridade.
    status_order = Case(
        When(status=ActionItem.Status.PENDING, then=Value(0)),
        When(status=ActionItem.Status.IN_PROGRESS, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    priority_order = Case(
        When(priority=ActionItem.Priority.CRITICAL, then=Value(0)),
        When(priority=ActionItem.Priority.HIGH, then=Value(1)),
        When(priority=ActionItem.Priority.MEDIUM, then=Value(2)),
        default=Value(3),
        output_field=IntegerField(),
    )
    return ActionItem.objects.annotate(
        status_order=status_order,
        priority_order=priority_order,
    ).order_by("status_order", "priority_order", "-created_at")


def update_action_status(action: ActionItem, new_status: str) -> ActionItem:
    open_statuses = [ActionItem.Status.PENDING, ActionItem.Status.IN_PROGRESS]
    try:
        with transaction.atomic():
            ActionItem.objects.select_for_update().filter(pk=action.pk).exists()
            # Reabrir também respeita a proteção contra duas ações abertas equivalentes.
            if new_status in open_statuses:
                existing = (
                    ActionItem.objects.select_for_update()
                    .filter(
                        source_alert_key=action.source_alert_key,
                        recommendation_key=action.recommendation_key,
                        status__in=open_statuses,
                    )
                    .exclude(pk=action.pk)
                    .first()
                )
                if existing:
                    raise DuplicateActionError(existing)
            action.status = new_status
            action.save(update_fields=["status", "updated_at"])
            return action
    except IntegrityError:
        existing = ActionItem.objects.get(
            source_alert_key=action.source_alert_key,
            recommendation_key=action.recommendation_key,
            status__in=open_statuses,
        )
        raise DuplicateActionError(existing) from None
