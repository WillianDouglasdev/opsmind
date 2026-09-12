"""Endpoints somente leitura para investigações derivadas da operação."""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from operations.investigations import (
    InvestigationNotFound,
    build_delivery_delay_investigation,
    list_investigations,
)
from operations.serializers import (
    DeliveryDelayInvestigationSerializer,
    InvestigationDetailQuerySerializer,
    InvestigationListSerializer,
    OperationPeriodQuerySerializer,
)


def _validated_query(serializer_class, request: Request) -> dict:
    serializer = serializer_class(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


@api_view(["GET"])
def investigation_collection(request: Request) -> Response:
    query = _validated_query(OperationPeriodQuerySerializer, request)
    payload = list_investigations(query["days"])
    return Response(InvestigationListSerializer(payload).data)


@api_view(["GET"])
def delivery_delay_investigation(request: Request) -> Response:
    query = _validated_query(InvestigationDetailQuerySerializer, request)
    try:
        payload = build_delivery_delay_investigation(
            days=query["days"],
            branch_id=query.get("branch"),
        )
    except InvestigationNotFound as error:
        return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
    return Response(DeliveryDelayInvestigationSerializer(payload).data)
