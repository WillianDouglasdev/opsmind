"""Fronteira HTTP: valida entradas, chama os serviços e traduz erros de domínio.

Novos cálculos pertencem a analytics/ ou ao serviço do domínio. Ingestão e ETL
devem ter uma entrada própria por comando, sem executar cargas durante um GET.
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from operations.alerts import AlertNotFound, build_investigation, get_active_alerts
from operations.actions import (
    DuplicateActionError,
    RecommendationNotFound,
    create_action_item,
    get_alert_recommendations,
    list_action_items,
    update_action_status,
)
from operations.analytics import (
    build_dashboard_changes,
    build_dashboard_summary,
    build_dashboard_trends,
)
from operations.ai import executive_summary, query_assistant
from operations.ai.providers import AIConfigurationError
from operations.models import ActionItem
from operations.pipelines import get_pipeline_detail, get_pipeline_run, list_pipelines
from operations.serializers import (
    ActionItemSerializer,
    AlertInvestigationSerializer,
    AlertSerializer,
    AssistantQuerySerializer,
    AssistantResponseSerializer,
    CreateActionSerializer,
    DashboardChangesSerializer,
    DashboardSummarySerializer,
    DashboardTrendsSerializer,
    PipelineRunSerializer,
    PipelineSummarySerializer,
    RecommendationSerializer,
    UpdateActionStatusSerializer,
)


@api_view(["GET"])
def dashboard_summary(_request: Request) -> Response:
    serializer = DashboardSummarySerializer(build_dashboard_summary())
    return Response(serializer.data)


@api_view(["GET"])
def dashboard_trends(_request: Request) -> Response:
    serializer = DashboardTrendsSerializer(build_dashboard_trends())
    return Response(serializer.data)


@api_view(["GET"])
def dashboard_changes(_request: Request) -> Response:
    serializer = DashboardChangesSerializer(build_dashboard_changes())
    return Response(serializer.data)


@api_view(["GET"])
def pipeline_collection(_request: Request) -> Response:
    return Response(PipelineSummarySerializer(list_pipelines(), many=True).data)


@api_view(["GET"])
def pipeline_detail(_request: Request, pipeline_key: str) -> Response:
    pipeline = get_pipeline_detail(pipeline_key)
    if pipeline is None:
        return Response(
            {"detail": "Pipeline não encontrada."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(PipelineSummarySerializer(pipeline).data)


@api_view(["GET"])
def pipeline_run_detail(_request: Request, pipeline_key: str, run_id: int) -> Response:
    run = get_pipeline_run(pipeline_key, run_id)
    if run is None:
        return Response(
            {"detail": "Execução de pipeline não encontrada."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(PipelineRunSerializer(run).data)


@api_view(["GET"])
def alert_list(_request: Request) -> Response:
    serializer = AlertSerializer(get_active_alerts(), many=True)
    return Response(serializer.data)


@api_view(["GET"])
def alert_investigation(_request: Request, alert_key: str) -> Response:
    try:
        investigation = build_investigation(alert_key)
    except AlertNotFound:
        return Response(
            {"detail": "Alerta não encontrado ou não está ativo."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = AlertInvestigationSerializer(investigation)
    return Response(serializer.data)


@api_view(["GET"])
def alert_recommendations(_request: Request, alert_key: str) -> Response:
    try:
        recommendations = get_alert_recommendations(alert_key)
    except AlertNotFound:
        return Response(
            {"detail": "Alerta não encontrado ou não está ativo."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = RecommendationSerializer(recommendations, many=True)
    return Response(serializer.data)


def _action_serializer(action_items, many: bool = False) -> ActionItemSerializer:
    # A origem é resolvida em lote porque Alert não é um model persistido.
    alert_titles = {alert["key"]: alert["title"] for alert in get_active_alerts()}
    return ActionItemSerializer(
        action_items,
        many=many,
        context={"alert_titles": alert_titles},
    )


@api_view(["GET", "POST"])
def action_collection(request: Request) -> Response:
    if request.method == "GET":
        return Response(_action_serializer(list_action_items(), many=True).data)

    # O payload contém só chaves; os textos oficiais são recuperados pelo service.
    input_serializer = CreateActionSerializer(data=request.data)
    input_serializer.is_valid(raise_exception=True)
    data = input_serializer.validated_data
    try:
        action = create_action_item(data["alert_key"], data["recommendation_key"])
    except AlertNotFound:
        return Response(
            {"detail": "Alerta não encontrado ou não está ativo."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except RecommendationNotFound:
        return Response(
            {"detail": "Recomendação não encontrada para este alerta."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except DuplicateActionError as error:
        return Response(
            {
                "detail": "A ação já está no plano.",
                "action": _action_serializer(error.action).data,
            },
            status=status.HTTP_409_CONFLICT,
        )
    return Response(
        _action_serializer(action).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
def action_detail(request: Request, action_id: int) -> Response:
    try:
        action = ActionItem.objects.get(pk=action_id)
    except ActionItem.DoesNotExist:
        return Response(
            {"detail": "Ação não encontrada."},
            status=status.HTTP_404_NOT_FOUND,
        )
    input_serializer = UpdateActionStatusSerializer(data=request.data)
    input_serializer.is_valid(raise_exception=True)
    try:
        action = update_action_status(action, input_serializer.validated_data["status"])
    except DuplicateActionError as error:
        return Response(
            {
                "detail": "Já existe uma ação aberta para esta recomendação.",
                "action": _action_serializer(error.action).data,
            },
            status=status.HTTP_409_CONFLICT,
        )
    return Response(_action_serializer(action).data)


@api_view(["POST"])
def assistant_query(request: Request) -> Response:
    input_serializer = AssistantQuerySerializer(data=request.data)
    input_serializer.is_valid(raise_exception=True)
    try:
        result = query_assistant(input_serializer.validated_data["question"])
    except AIConfigurationError as error:
        return Response(
            {"detail": str(error)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    output_serializer = AssistantResponseSerializer(result)
    return Response(output_serializer.data)


@api_view(["POST"])
def assistant_executive_summary(_request: Request) -> Response:
    try:
        result = executive_summary()
    except AIConfigurationError as error:
        return Response(
            {"detail": str(error)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    serializer = AssistantResponseSerializer(result)
    return Response(serializer.data)
