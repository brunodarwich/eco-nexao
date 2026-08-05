import re
import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import RawAnalyticsEvent

OPERATIONAL_EVENT_DIMENSIONS = {
    "session_opened": frozenset({"region_id"}),
    "route_opened": frozenset({"region_id", "route_id"}),
    "contact_opened": frozenset({"region_id", "route_id", "actor_id"}),
    "offline_download_completed": frozenset({"region_id", "route_id"}),
}
ALLOWED_EVENTS = frozenset(OPERATIONAL_EVENT_DIMENSIONS)
EVENT_INPUT_FIELDS = frozenset(
    {
        "event_id",
        "event_name",
        "schema_version",
        "occurred_at",
        "region_id",
        "route_id",
        "actor_id",
    }
)
FORBIDDEN_KEY_PATTERN = re.compile(
    r"(name|nome|email|phone|telefone|cpf|lat|lng|longitude|latitude|ip|address|"
    r"endereco|query|text|texto|message|mensagem|url|comment|user|session|consent|device)",
    re.IGNORECASE,
)


class AnalyticsEventInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawAnalyticsEvent
        fields = (
            "event_id",
            "event_name",
            "schema_version",
            "occurred_at",
            "region_id",
            "route_id",
            "actor_id",
        )
        extra_kwargs = {
            "event_id": {"required": True},
            "schema_version": {"required": False},
            "region_id": {"required": True, "allow_blank": False},
            "route_id": {"required": False},
            "actor_id": {"required": False},
        }

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Cada evento deve ser um objeto JSON.")
        unknown = set(data) - EVENT_INPUT_FIELDS
        if unknown:
            forbidden = sorted(key for key in unknown if FORBIDDEN_KEY_PATTERN.search(key))
            if forbidden:
                raise serializers.ValidationError(
                    {"forbidden_fields": forbidden, "detail": "Dados pessoais são proibidos."}
                )
            raise serializers.ValidationError({"unknown_fields": sorted(unknown)})
        return super().to_internal_value(data)

    def validate_event_name(self, value):
        if value not in ALLOWED_EVENTS:
            raise serializers.ValidationError("Evento não permitido pela allowlist operacional.")
        return value

    def validate_occurred_at(self, value):
        now = timezone.now()
        if value > now + timedelta(minutes=5):
            raise serializers.ValidationError("O horário do evento não pode estar no futuro.")
        if value < now - timedelta(hours=24):
            raise serializers.ValidationError("Evento fora da janela de ingestão de 24 horas.")
        return value

    def validate_actor_id(self, value):
        if not value:
            return value
        try:
            return str(uuid.UUID(value))
        except (TypeError, ValueError, AttributeError) as exc:
            raise serializers.ValidationError("Ponto de apoio deve ser um UUID válido.") from exc

    def validate(self, attrs):
        event_name = attrs["event_name"]
        allowed = OPERATIONAL_EVENT_DIMENSIONS[event_name]
        provided = {key for key in ("region_id", "route_id", "actor_id") if attrs.get(key)}
        if provided - allowed:
            raise serializers.ValidationError("Dimensão não permitida para este evento.")
        if event_name != "session_opened" and not attrs.get("route_id"):
            raise serializers.ValidationError({"route_id": "Rota é obrigatória."})
        if event_name == "contact_opened" and not attrs.get("actor_id"):
            raise serializers.ValidationError({"actor_id": "Ponto de apoio é obrigatório."})
        return attrs


class AnalyticsBatchSerializer(serializers.Serializer):
    consent_granted = serializers.BooleanField()
    events = AnalyticsEventInputSerializer(many=True)

    def validate_consent_granted(self, value):
        if value is not True:
            raise serializers.ValidationError("Consentimento de analytics é obrigatório.")
        return value

    def validate_events(self, value):
        if not value:
            raise serializers.ValidationError("O lote de eventos não pode ser vazio.")
        if len(value) > 50:
            raise serializers.ValidationError("O lote não pode conter mais de 50 eventos.")
        return value


class AnalyticsBatchResponseSerializer(serializers.Serializer):
    received = serializers.IntegerField(min_value=0)
    status = serializers.CharField()


class DailyAnalyticsAggregateSerializer(serializers.Serializer):
    date = serializers.DateField()
    event_name = serializers.CharField()
    region_slug = serializers.CharField()
    route_slug = serializers.CharField()
    count = serializers.IntegerField(min_value=0)


class AnalyticsSummaryResponseSerializer(serializers.Serializer):
    total_events = serializers.IntegerField(min_value=0)
    aggregates = DailyAnalyticsAggregateSerializer(many=True)


class AnalyticsMetricSerializer(serializers.Serializer):
    event_name = serializers.ChoiceField(choices=sorted(ALLOWED_EVENTS))
    count = serializers.IntegerField(min_value=10, allow_null=True)
    suppressed = serializers.BooleanField()


class SupportPointRankingSerializer(serializers.Serializer):
    support_point_id = serializers.UUIDField()
    support_point_name = serializers.CharField()
    contacts = serializers.IntegerField(min_value=10)


class OperationalAnalyticsResponseSerializer(serializers.Serializer):
    region_slug = serializers.CharField()
    route_slug = serializers.CharField(allow_blank=True)
    start = serializers.DateField()
    end = serializers.DateField()
    privacy_threshold = serializers.IntegerField(min_value=10)
    metrics = AnalyticsMetricSerializer(many=True)
    ranking = SupportPointRankingSerializer(many=True)
