import re
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import RawAnalyticsEvent

EVENT_PROPERTY_SCHEMAS = {
    # Aplicação e navegação
    "app_opened": {"entry_type": (str, ["direct", "link", "shortcut", "notification"])},
    "screen_viewed": {"screen_name": str, "previous_screen": str},
    "navigation_clicked": {"target": str, "label": str},
    "back_clicked": {"from_screen": str},
    "cta_clicked": {"cta_id": str, "location": str},
    "region_selector_opened": {},
    "region_selected": {"region_id": str, "previous_region_id": str},
    "interest_selected": {"interest": str, "selected": bool},
    "search_submitted": {"has_results": bool, "results_count": int},
    "filters_opened": {"screen": str},
    "filters_applied": {"filter_type": str, "count": int},
    "filters_cleared": {"screen": str},
    "sort_changed": {"sort_by": str},
    # Rotas
    "route_card_clicked": {"route_id": str, "position": int},
    "route_viewed": {"route_id": str, "source": str, "offline_capable": (str, bool)},
    "route_tab_selected": {"route_id": str, "tab": str},
    "route_started": {"route_id": str},
    "route_completed": {"route_id": str, "duration_minutes": int},
    "stage_opened": {"route_id": str, "stage_id": str},
    "stage_marked_completed": {"route_id": str, "stage_id": str},
    "favorite_toggled": {"target_type": str, "target_id": str, "is_favorite": bool},
    "share_clicked": {"target_type": str, "target_id": str, "method": str},
    "alert_viewed": {"alert_id": str, "alert_type": str},
    "sources_opened": {"target_id": str},
    "support_point_clicked": {"point_id": str, "point_type": str},
    # Mapa
    "map_opened": {"source": str},
    "map_marker_clicked": {"target_type": str, "target_id": str},
    "map_item_opened": {"target_type": str, "target_id": str},
    "map_layers_opened": {},
    "map_layer_toggled": {"layer_id": str, "enabled": bool},
    "map_list_opened": {},
    "map_recentered": {},
    "location_permission_requested": {},
    "location_permission_result": {"granted": bool},
    "external_navigation_clicked": {"destination_type": str},
    # Catálogo e contatos
    "route_catalog_viewed": {"category": str},
    "catalog_search_submitted": {"has_results": bool},
    "catalog_category_selected": {"category_id": str},
    "catalog_filters_opened": {},
    "catalog_filters_applied": {"count": int},
    "catalog_item_clicked": {"item_id": str, "category": str},
    "actor_viewed": {"actor_id": str, "category": str},
    "actor_contact_clicked": {"actor_id": str, "contact_type": str},
    "route_context_clicked": {"context_id": str},
    # Offline
    "offline_download_started": {"package_id": str, "size_mb": (int, float)},
    "offline_download_completed": {"package_id": str, "duration_seconds": int},
    "offline_download_failed": {"package_id": str, "error_code": str},
    "offline_update_started": {"package_id": str},
    "offline_download_removed": {"package_id": str},
    "offline_package_opened": {"package_id": str},
    # Perfil e privacidade
    "profile_preferences_opened": {},
    "profile_preferences_saved": {"preference_type": str},
    "offline_manager_opened": {},
    "privacy_center_opened": {},
    "consent_settings_opened": {},
    "consent_changed": {"analytics_opt_in": bool},
    "local_data_cleared": {},
    "privacy_request_opened": {"request_type": str},
    # Relatos e qualidade
    "issue_report_opened": {"target_type": str, "target_id": str},
    "issue_report_queued": {"report_id": str},
    "issue_report_submitted": {"report_id": str},
    "feedback_submitted": {"score": int},
    "app_error": {"error_code": str, "component": str},
}

ALLOWED_EVENTS = set(EVENT_PROPERTY_SCHEMAS.keys())

FORBIDDEN_PII_KEYS = {
    "name",
    "nome",
    "email",
    "phone",
    "telefone",
    "cpf",
    "latitude",
    "longitude",
    "lat",
    "lng",
    "user_agent",
    "user_id",
    "ip",
    "address",
    "endereco",
    "query",
    "text",
    "texto",
    "message",
    "mensagem",
    "url",
    "comment",
    "comentario",
}

EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")


def validate_no_pii_recursive(data):
    """
    Inspeciona recursivamente chaves e valores rejeitando PII, coordenadas e texto livre.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in FORBIDDEN_PII_KEYS:
                raise serializers.ValidationError(
                    {"properties": f"Propriedades contêm chave de dados pessoais/proibida: '{k}'."}
                )
            validate_no_pii_recursive(v)
    elif isinstance(data, list):
        for item in data:
            validate_no_pii_recursive(item)
    elif isinstance(data, str):
        if len(data) > 100:
            raise serializers.ValidationError(
                {
                    "properties": (
                        "Valores de texto em propriedades de analytics "
                        "não podem exceder 100 caracteres."
                    )
                }
            )
        if EMAIL_REGEX.search(data):
            raise serializers.ValidationError(
                {"properties": "Valor de propriedade contém endereço de e-mail proibido."}
            )


class AnalyticsEventInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawAnalyticsEvent
        fields = [
            "event_id",
            "event_name",
            "schema_version",
            "occurred_at",
            "anonymous_id",
            "session_id",
            "consent_id",
            "consent_version",
            "app_version",
            "screen_name",
            "region_id",
            "route_id",
            "actor_id",
            "stage_id",
            "source",
            "campaign_id",
            "device_class",
            "network_class",
            "display_mode",
            "properties",
        ]

    def validate_event_name(self, value):
        if value not in ALLOWED_EVENTS:
            raise serializers.ValidationError(
                f"Evento '{value}' não é permitido pela taxonomia de analytics."
            )
        return value

    def validate_occurred_at(self, value):
        now = timezone.now()
        if value > now + timedelta(minutes=5):
            raise serializers.ValidationError("O horário do evento não pode estar no futuro.")
        if value < now - timedelta(days=90):
            raise serializers.ValidationError(
                "O horário do evento é anterior à janela de retenção de 90 dias."
            )
        return value

    def validate(self, attrs):
        event_name = attrs.get("event_name")
        properties = attrs.get("properties", {})

        if not isinstance(properties, dict):
            raise serializers.ValidationError(
                {"properties": "As propriedades devem ser um objeto JSON."}
            )

        # Checagem de PII e texto estrito
        validate_no_pii_recursive(properties)

        # Validação estrita contra a allowlist do evento
        allowed_schema = EVENT_PROPERTY_SCHEMAS.get(event_name, {})
        for prop_key, prop_val in properties.items():
            if prop_key not in allowed_schema:
                raise serializers.ValidationError(
                    {
                        "properties": (
                            f"Propriedade '{prop_key}' não é permitida "
                            f"para o evento '{event_name}'."
                        )
                    }
                )

            expected_spec = allowed_schema[prop_key]
            if (
                isinstance(expected_spec, tuple)
                and len(expected_spec) == 2
                and isinstance(expected_spec[1], list)
            ):
                expected_type, allowed_values = expected_spec
                if not isinstance(prop_val, expected_type) or prop_val not in allowed_values:
                    raise serializers.ValidationError(
                        {
                            "properties": (
                                f"Valor '{prop_val}' para a propriedade '{prop_key}' "
                                f"deve ser um dos seguintes: {allowed_values}."
                            )
                        }
                    )
            elif isinstance(expected_spec, tuple):
                if not isinstance(prop_val, expected_spec):
                    raise serializers.ValidationError(
                        {
                            "properties": (
                                f"Tipo inválido para a propriedade '{prop_key}' "
                                f"do evento '{event_name}'."
                            )
                        }
                    )
            elif isinstance(expected_spec, type):
                if not isinstance(prop_val, expected_spec):
                    raise serializers.ValidationError(
                        {
                            "properties": (
                                f"Tipo inválido para a propriedade '{prop_key}' "
                                f"do evento '{event_name}'."
                            )
                        }
                    )

        return attrs


class AnalyticsBatchSerializer(serializers.Serializer):
    events = AnalyticsEventInputSerializer(many=True)

    def validate_events(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("O lote de eventos não pode ser vazio.")
        if len(value) > 50:
            raise serializers.ValidationError("O lote de eventos não pode conter mais de 50 itens.")
        return value
