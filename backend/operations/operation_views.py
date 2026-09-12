"""Endpoints de leitura para a navegação progressiva da área Operação."""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from operations.operation import (
    OperationNotFound,
    build_branch_detail,
    build_delay_overview,
    build_operation_overview,
    list_operation_orders,
)
from operations.serializers import (
    DelayOverviewSerializer,
    OperationBranchDetailSerializer,
    OperationOrderPageSerializer,
    OperationOrdersQuerySerializer,
    OperationOverviewSerializer,
    OperationPeriodQuerySerializer,
)


def _validated_query(serializer_class, request: Request) -> dict:
    serializer = serializer_class(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


@api_view(["GET"])
def operation_overview(request: Request) -> Response:
    query = _validated_query(OperationPeriodQuerySerializer, request)
    return Response(OperationOverviewSerializer(build_operation_overview(query["days"])).data)


@api_view(["GET"])
def operation_delays(request: Request) -> Response:
    query = _validated_query(OperationPeriodQuerySerializer, request)
    return Response(DelayOverviewSerializer(build_delay_overview(query["days"])).data)


@api_view(["GET"])
def operation_branch_detail(request: Request, branch_id: int) -> Response:
    query = _validated_query(OperationPeriodQuerySerializer, request)
    try:
        payload = build_branch_detail(branch_id, query["days"])
    except OperationNotFound as error:
        return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
    return Response(OperationBranchDetailSerializer(payload).data)


@api_view(["GET"])
def operation_orders(request: Request) -> Response:
    query = _validated_query(OperationOrdersQuerySerializer, request)
    try:
        payload = list_operation_orders(
            days=query["days"],
            branch_id=query.get("branch"),
            status=query["status"],
            delivery=query["delivery"],
            page=query["page"],
            page_size=query["page_size"],
        )
    except ValueError as error:
        return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(OperationOrderPageSerializer(payload).data)
