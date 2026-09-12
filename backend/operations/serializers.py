"""Contratos públicos entre os serviços Python e o frontend.

Serializers comuns representam dicionários calculados; ActionItemSerializer lê um
model persistido. Instanciar um serializer de saída não executa is_valid(): os testes
de contrato também precisam proteger as formas e os tipos produzidos pelos serviços.
"""

from rest_framework import serializers

from operations.models import ActionItem, Order


class StrictFieldsMixin:
    def validate(self, attrs):
        # Rejeitamos campos extras para o cliente não pensar que título ou prioridade foram aceitos.
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError(
                {field: "Campo não permitido." for field in sorted(unknown_fields)}
            )
        return super().validate(attrs)


class HealthComponentSerializer(serializers.Serializer):
    name = serializers.CharField()
    impact = serializers.IntegerField()
    value = serializers.FloatField()
    unit = serializers.CharField()


class OperationalHealthSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=100)
    status = serializers.CharField()
    description = serializers.CharField()
    components = HealthComponentSerializer(many=True)


class RevenueMetricSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=16, decimal_places=2)
    change_percentage = serializers.FloatField(allow_null=True)


class CountMetricSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    change_percentage = serializers.FloatField(allow_null=True)


class DelayedOrderMetricSerializer(CountMetricSerializer):
    rate = serializers.FloatField()


class ActiveTicketMetricSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    total_tickets = serializers.IntegerField()
    active_rate = serializers.FloatField()
    definition = serializers.CharField()


class DashboardSummarySerializer(serializers.Serializer):
    reference_date = serializers.DateField()
    operational_health = OperationalHealthSerializer()
    revenue = RevenueMetricSerializer()
    orders = CountMetricSerializer()
    delayed_orders = DelayedOrderMetricSerializer()
    open_tickets = ActiveTicketMetricSerializer()


class TrendPointSerializer(serializers.Serializer):
    month = serializers.CharField()
    label = serializers.CharField()
    value = serializers.FloatField(min_value=0, max_value=100)
    total_orders = serializers.IntegerField(min_value=0)


class DashboardTrendsSerializer(serializers.Serializer):
    reference_date = serializers.DateField()
    metric = serializers.CharField()
    target = serializers.FloatField()
    series = TrendPointSerializer(many=True)


class ChangeItemSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["percentage", "inventory"])
    label = serializers.CharField()
    value = serializers.FloatField(allow_null=True)
    direction = serializers.ChoiceField(choices=["up", "down", "neutral", "current"])
    tone = serializers.ChoiceField(choices=["positive", "negative", "neutral", "warning"])
    description = serializers.CharField()


class DashboardChangesSerializer(serializers.Serializer):
    reference_date = serializers.DateField()
    items = ChangeItemSerializer(many=True)


class PipelineStepSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["pending", "running", "success", "warning", "failed"]
    )
    records = serializers.IntegerField(allow_null=True, min_value=0)


class PipelineIssueSerializer(serializers.Serializer):
    record_identifier = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()
    detected_at = serializers.DateTimeField()


class PipelineRunSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    pipeline_key = serializers.CharField()
    status = serializers.ChoiceField(choices=["running", "success", "warning", "failed"])
    source_name = serializers.CharField()
    started_at = serializers.DateTimeField()
    finished_at = serializers.DateTimeField(allow_null=True)
    published_at = serializers.DateTimeField(allow_null=True)
    duration_seconds = serializers.FloatField(allow_null=True, min_value=0)
    records_received = serializers.IntegerField(min_value=0)
    records_valid = serializers.IntegerField(min_value=0)
    records_rejected = serializers.IntegerField(min_value=0)
    records_loaded = serializers.IntegerField(min_value=0)
    quality_percentage = serializers.FloatField(allow_null=True, min_value=0, max_value=100)
    steps = serializers.DictField(child=PipelineStepSerializer())
    error_message = serializers.CharField(allow_blank=True)
    issues = PipelineIssueSerializer(many=True, required=False)


class PipelineSummarySerializer(serializers.Serializer):
    pipeline_key = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    latest_run = PipelineRunSerializer(allow_null=True)
    last_published_at = serializers.DateTimeField(allow_null=True)
    recent_runs = PipelineRunSerializer(many=True, required=False)


class OperationPeriodQuerySerializer(StrictFieldsMixin, serializers.Serializer):
    days = serializers.IntegerField(required=False, default=30)

    def validate_days(self, value):
        if value not in (7, 30, 90):
            raise serializers.ValidationError("Use 7, 30 ou 90 dias.")
        return value


class OperationOrdersQuerySerializer(OperationPeriodQuerySerializer):
    branch = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    status = serializers.ChoiceField(
        choices=["", *Order.Status.values], required=False, default="", allow_blank=True,
    )
    delivery = serializers.ChoiceField(
        choices=["all", "late"], required=False, default="all",
    )
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=15, min_value=1, max_value=50)


class OperationPeriodSerializer(serializers.Serializer):
    days = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reference_date = serializers.DateField()


class MetricDefinitionSerializer(serializers.Serializer):
    metric_key = serializers.CharField()
    entity = serializers.CharField()
    field = serializers.CharField()
    rule = serializers.CharField()
    pipeline_key = serializers.CharField()


class BranchHealthSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=100)
    status = serializers.CharField()


class OperationBranchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    orders = serializers.IntegerField(min_value=0)
    delayed_orders = serializers.IntegerField(min_value=0)
    delay_rate = serializers.FloatField(min_value=0, max_value=100)
    previous_delay_rate = serializers.FloatField(min_value=0, max_value=100)
    revenue = serializers.DecimalField(max_digits=16, decimal_places=2)
    customers = serializers.IntegerField(min_value=0)
    impacted_customers = serializers.IntegerField(min_value=0)
    strategic_customers = serializers.IntegerField(min_value=0)
    impacted_strategic_customers = serializers.IntegerField(min_value=0)
    active_tickets = serializers.IntegerField(min_value=0)
    total_tickets = serializers.IntegerField(min_value=0)
    critical_inventory = serializers.IntegerField(min_value=0)
    inventory_items = serializers.IntegerField(min_value=0)
    health = BranchHealthSerializer(allow_null=True)


class BranchAverageSerializer(serializers.Serializer):
    orders = serializers.FloatField(allow_null=True)
    delay_rate = serializers.FloatField(allow_null=True)
    revenue = serializers.DecimalField(max_digits=16, decimal_places=2, allow_null=True)
    active_tickets = serializers.FloatField(allow_null=True)
    health_score = serializers.FloatField(allow_null=True)


class CriticalProductSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    affected_branches = serializers.IntegerField(min_value=0)
    available = serializers.IntegerField(min_value=0)
    minimum = serializers.IntegerField(min_value=0)
    deficit = serializers.IntegerField(min_value=0)


class OperationMetricsSerializer(serializers.Serializer):
    orders = serializers.IntegerField(min_value=0)
    delayed_orders = serializers.IntegerField(min_value=0)
    delay_rate = serializers.FloatField(min_value=0, max_value=100)
    revenue = serializers.DecimalField(max_digits=16, decimal_places=2)
    customers = serializers.IntegerField(min_value=0)
    active_tickets = serializers.IntegerField(min_value=0)
    critical_inventory = serializers.IntegerField(min_value=0)


class OperationAttentionSerializer(serializers.Serializer):
    worst_branch = OperationBranchSerializer(allow_null=True)
    critical_products = CriticalProductSerializer(many=True)
    strategic_customers_impacted = serializers.IntegerField(min_value=0)


class OperationOverviewSerializer(serializers.Serializer):
    period = OperationPeriodSerializer()
    metrics = OperationMetricsSerializer()
    branch_average = BranchAverageSerializer()
    branches = OperationBranchSerializer(many=True)
    attention = OperationAttentionSerializer()
    metric_definition = MetricDefinitionSerializer()


class BranchIdentitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()


class BranchComparisonSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    unit = serializers.ChoiceField(choices=["percentage", "count", "currency", "score"])
    branch_value = serializers.JSONField(allow_null=True)
    average_value = serializers.JSONField(allow_null=True)
    difference = serializers.JSONField(allow_null=True)


class BranchTrendPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    orders = serializers.IntegerField(min_value=0)
    delayed_orders = serializers.IntegerField(min_value=0)
    delay_rate = serializers.FloatField(min_value=0, max_value=100)
    revenue = serializers.DecimalField(max_digits=16, decimal_places=2)


class OperationBranchDetailSerializer(serializers.Serializer):
    period = OperationPeriodSerializer()
    branch = BranchIdentitySerializer()
    metrics = OperationBranchSerializer()
    comparison_scope = serializers.CharField()
    comparisons = BranchComparisonSerializer(many=True)
    trend = BranchTrendPointSerializer(many=True)
    metric_definition = MetricDefinitionSerializer()


class DelayMetricsSerializer(serializers.Serializer):
    orders = serializers.IntegerField(min_value=0)
    delayed_orders = serializers.IntegerField(min_value=0)
    delay_rate = serializers.FloatField(min_value=0, max_value=100)
    impacted_customers = serializers.IntegerField(min_value=0)


class DelayBranchSerializer(OperationBranchSerializer):
    contribution_percentage = serializers.FloatField(min_value=0, max_value=100)


class DelayOverviewSerializer(serializers.Serializer):
    period = OperationPeriodSerializer()
    metrics = DelayMetricsSerializer()
    branches = DelayBranchSerializer(many=True)
    metric_definition = MetricDefinitionSerializer()


class OrderReferenceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class OperationOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    identifier = serializers.CharField()
    customer = OrderReferenceSerializer()
    branch = OrderReferenceSerializer()
    created_at = serializers.DateTimeField()
    promised_at = serializers.DateTimeField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    status = serializers.ChoiceField(choices=Order.Status.values)
    status_label = serializers.CharField()
    delivery_state = serializers.CharField()
    delivery_state_label = serializers.CharField()


class OperationOrderPageSerializer(serializers.Serializer):
    period = OperationPeriodSerializer()
    count = serializers.IntegerField(min_value=0)
    page = serializers.IntegerField(min_value=1)
    page_size = serializers.IntegerField(min_value=1)
    total_pages = serializers.IntegerField(min_value=1)
    results = OperationOrderSerializer(many=True)


class InvestigationDetailQuerySerializer(OperationPeriodQuerySerializer):
    branch = serializers.IntegerField(required=False, min_value=1, allow_null=True)


class InvestigationListItemSerializer(serializers.Serializer):
    key = serializers.CharField()
    type = serializers.ChoiceField(choices=["delivery_delays"])
    title = serializers.CharField()
    description = serializers.CharField()
    severity = serializers.ChoiceField(choices=["low", "medium", "high", "critical"])
    branch = BranchIdentitySerializer()
    delay_rate = serializers.FloatField(min_value=0, max_value=100)
    delayed_orders = serializers.IntegerField(min_value=0)
    detail_url = serializers.CharField()


class InvestigationListSerializer(serializers.Serializer):
    period = OperationPeriodSerializer()
    items = InvestigationListItemSerializer(many=True)


class InvestigationValueSerializer(serializers.Serializer):
    label = serializers.CharField()
    value = serializers.JSONField(allow_null=True)
    unit = serializers.ChoiceField(
        choices=["count", "currency", "percentage", "percentage_change", "percentage_points"]
    )


class OperationalEvidenceSerializer(serializers.Serializer):
    key = serializers.CharField()
    type = serializers.ChoiceField(choices=["delivery", "tickets", "inventory", "customers"])
    title = serializers.CharField()
    description = serializers.CharField()
    current = InvestigationValueSerializer()
    comparison = InvestigationValueSerializer(allow_null=True)
    difference = InvestigationValueSerializer(allow_null=True)
    change = InvestigationValueSerializer(allow_null=True)
    importance = serializers.ChoiceField(choices=["primary", "related"])
    source = serializers.CharField()
    detail_url = serializers.CharField(allow_null=True)


class InvestigationSummarySerializer(serializers.Serializer):
    title = serializers.CharField()
    situation = serializers.CharField()
    severity = serializers.ChoiceField(choices=["low", "medium", "high", "critical"])
    branch = BranchIdentitySerializer()
    branch_delay_rate = serializers.FloatField(min_value=0, max_value=100)
    operation_delay_rate = serializers.FloatField(min_value=0, max_value=100)
    difference_percentage_points = serializers.FloatField()
    previous_delay_rate = serializers.FloatField(min_value=0, max_value=100)
    change_percentage = serializers.FloatField(allow_null=True)
    delayed_orders = serializers.IntegerField(min_value=0)
    impacted_customers = serializers.IntegerField(min_value=0)
    affected_revenue = serializers.DecimalField(max_digits=16, decimal_places=2)


class InvestigationTimelineItemSerializer(serializers.Serializer):
    date = serializers.DateField()
    type = serializers.ChoiceField(choices=["delayed_orders"])
    title = serializers.CharField()
    description = serializers.CharField()
    value = serializers.IntegerField(min_value=0)
    unit = serializers.ChoiceField(choices=["count"])
    source = serializers.CharField()
    detail_url = serializers.CharField(allow_null=True)


class InvestigationNextStepSerializer(serializers.Serializer):
    key = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    detail_url = serializers.CharField(allow_null=True)


class InvestigationNavigationSerializer(serializers.Serializer):
    investigations_url = serializers.CharField()
    operation_url = serializers.CharField()


class DeliveryDelayInvestigationSerializer(serializers.Serializer):
    key = serializers.CharField()
    type = serializers.ChoiceField(choices=["delivery_delays"])
    data_status = serializers.ChoiceField(choices=["empty", "partial", "complete"])
    period = OperationPeriodSerializer()
    summary = InvestigationSummarySerializer(allow_null=True)
    evidence = OperationalEvidenceSerializer(many=True)
    timeline = InvestigationTimelineItemSerializer(many=True)
    next_steps = InvestigationNextStepSerializer(many=True)
    causality_notice = serializers.CharField()
    navigation = InvestigationNavigationSerializer()


class AlertMetricSerializer(serializers.Serializer):
    label = serializers.CharField()
    value = serializers.JSONField()
    unit = serializers.ChoiceField(
        choices=[
            "count",
            "currency",
            "percentage",
            "percentage_change",
            "percentage_points",
            "score",
            "text",
        ]
    )


class AlertSerializer(serializers.Serializer):
    key = serializers.CharField()
    type = serializers.CharField()
    severity = serializers.ChoiceField(choices=["low", "medium", "high", "critical"])
    title = serializers.CharField()
    summary = serializers.CharField()
    reference_date = serializers.DateField()
    metrics = AlertMetricSerializer(many=True)


class InvestigationSectionSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    metrics = AlertMetricSerializer(many=True)


class AlertInvestigationSerializer(serializers.Serializer):
    alert = AlertSerializer()
    context = serializers.CharField()
    impact = AlertMetricSerializer(many=True)
    related_signals = InvestigationSectionSerializer(many=True)
    evidence = InvestigationSectionSerializer(many=True)


class RecommendationSerializer(serializers.Serializer):
    recommendation_key = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    priority = serializers.ChoiceField(choices=ActionItem.Priority.values)
    reason = serializers.CharField()
    alert_key = serializers.CharField()
    alert_type = serializers.CharField()
    is_added = serializers.BooleanField()


class CreateActionSerializer(StrictFieldsMixin, serializers.Serializer):
    alert_key = serializers.CharField(max_length=120, trim_whitespace=True)
    recommendation_key = serializers.CharField(max_length=100, trim_whitespace=True)


class UpdateActionStatusSerializer(StrictFieldsMixin, serializers.Serializer):
    status = serializers.ChoiceField(choices=ActionItem.Status.values)


class ActionItemSerializer(serializers.ModelSerializer):
    source_alert_title = serializers.SerializerMethodField()

    class Meta:
        model = ActionItem
        fields = [
            "id",
            "recommendation_key",
            "title",
            "description",
            "source_alert_key",
            "source_alert_type",
            "source_alert_title",
            "priority",
            "status",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        # Criação e atualização usam contratos menores; a representação completa é só de saída.
        read_only_fields = fields

    def get_source_alert_title(self, action: ActionItem) -> str:
        titles = self.context.get("alert_titles", {})
        fallback = {
            "DELIVERY_DELAY_INCREASE": "Atrasos nas entregas aumentaram",
            "BRANCH_PERFORMANCE": "Desempenho da filial",
            "INVENTORY_RISK": "Produtos com estoque abaixo do mínimo",
            "STRATEGIC_CUSTOMER_RISK": "Clientes estratégicos com ocorrências recorrentes",
        }
        return titles.get(
            action.source_alert_key,
            fallback.get(action.source_alert_type, action.source_alert_type),
        )


class AssistantQuerySerializer(serializers.Serializer):
    # O limite evita enviar textos desnecessariamente grandes ao provider.
    question = serializers.CharField(
        allow_blank=False,
        max_length=500,
        trim_whitespace=True,
    )


class AssistantResponseSerializer(serializers.Serializer):
    intent = serializers.ChoiceField(
        choices=[
            "DELIVERY_DELAYS",
            "CUSTOMER_RISK",
            "INVENTORY_RISK",
            "BRANCH_PERFORMANCE",
            "TICKET_ANALYSIS",
            "EXECUTIVE_SUMMARY",
            "UNKNOWN",
        ]
    )
    confidence = serializers.FloatField(min_value=0, max_value=1)
    answer = serializers.CharField()
    evidence = AlertMetricSerializer(many=True)
    provider = serializers.ChoiceField(choices=["mock", "gemini", "fallback"])
