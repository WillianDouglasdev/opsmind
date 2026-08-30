from rest_framework import serializers

from operations.models import ActionItem


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
