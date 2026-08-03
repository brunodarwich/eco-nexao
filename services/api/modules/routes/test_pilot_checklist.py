"""Checklist editorial, acessível, offline e analítico — Tarefa 12.3.

Verifica que os contratos de dados das rotas satisfazem os requisitos
de publicação, acessibilidade, disponibilidade offline e conformidade
LGPD dos eventos de analytics.

Não requer banco de dados: testa contratos de serialização, filtros de
queryset e allowlists de campos declarados nas views e serializers.

_Requisitos: RF-01 a RF-13, RNF-01 a RNF-08_
"""

import uuid

import pytest
from django.utils import timezone

from modules.analytics.serializers import (
    ALLOWED_EVENTS,
    FORBIDDEN_PII_KEYS,
    AnalyticsEventInputSerializer,
)
from modules.routes.serializers import RouteDetailSerializer, RouteSummarySerializer
from modules.routes.views import RegionRouteListView, RouteDetailView

# ══════════════════════════════════════════════════════════════════════════════
# Checklist editorial
# ══════════════════════════════════════════════════════════════════════════════


def test_route_summary_exposes_required_editorial_fields():
    """RouteSummarySerializer inclui todos os campos exigidos para publicação."""
    required = {
        "id",
        "slug",
        "public_name",
        "short_promise",
        "duration_minutes",
        "difficulty",
        "updated_at",
    }
    declared = set(RouteSummarySerializer.Meta.fields)
    missing = required - declared
    assert not missing, f"Campos editoriais obrigatórios ausentes no resumo: {missing}"


def test_route_detail_view_requires_dual_publication_gate():
    """RouteDetailView exige publicação em region.status E editorial_status."""
    view = RouteDetailView()
    view.kwargs = {"region_slug": "regiao-exemplo", "route_slug": "rota-exemplo"}
    filters = repr(view.get_queryset().query.where).lower()
    assert filters.count("published") == 2, (
        "Somente rotas com region.status=PUBLISHED e editorial_status=PUBLISHED devem aparecer."
    )


def test_route_list_slug_filter_is_dynamic():
    """RegionRouteListView usa o slug da URL como filtro — nenhuma região está hardcoded."""
    for slug in ("area-a", "area-b", "destino-ecologico-c"):
        view = RegionRouteListView()
        view.kwargs = {"region_slug": slug}
        filters = repr(view.get_queryset().query.where)
        assert slug in filters.lower(), f"Slug '{slug}' não aplicado como filtro dinâmico."


# ══════════════════════════════════════════════════════════════════════════════
# Checklist de acessibilidade
# ══════════════════════════════════════════════════════════════════════════════


def test_route_summary_includes_accessibility_content_field():
    """O resumo da rota carrega accessibility_content para leitores de tela."""
    assert "accessibility_content" in RouteSummarySerializer.Meta.fields, (
        "accessibility_content deve estar na listagem para alternativa textual."
    )


def test_route_detail_includes_preparation_and_accessibility_content():
    """O detalhe da rota inclui preparation_content e accessibility_content."""
    fields = RouteDetailSerializer.Meta.fields
    assert "preparation_content" in fields
    assert "accessibility_content" in fields


def test_route_stage_serializer_has_text_alternative_fields():
    """RouteStageSerializer expõe campos de texto para alternativa acessível ao mapa."""
    from modules.routes.serializers import RouteStageSerializer

    fields = RouteStageSerializer.Meta.fields
    assert "public_name" in fields, "public_name é obrigatório para alternativa textual da etapa."
    assert "description" in fields, "description apoia leitores de tela ao navegar as etapas."
    assert "stage_type" in fields, "stage_type indica o papel semântico da etapa."
    assert "arrival_guidance" in fields, "arrival_guidance orienta a chegada por texto."


# ══════════════════════════════════════════════════════════════════════════════
# Checklist offline
# ══════════════════════════════════════════════════════════════════════════════


def test_route_summary_exposes_offline_enabled_flag():
    """offline_enabled está no resumo para que o cliente decida exibir o botão de download."""
    assert "offline_enabled" in RouteSummarySerializer.Meta.fields


def test_route_detail_includes_stages_and_segments_for_offline_pack():
    """O detalhe inclui stages e segments para montar o pacote offline completo."""
    fields = RouteDetailSerializer.Meta.fields
    assert "stages" in fields, "Etapas são obrigatórias para o pacote offline."
    assert "segments" in fields, "Segmentos GeoJSON são obrigatórios para o mapa offline."


# ══════════════════════════════════════════════════════════════════════════════
# Checklist de analytics / LGPD
# ══════════════════════════════════════════════════════════════════════════════


# Base mínima para um evento válido
def _base_event(event_name: str = "app_opened", **extra) -> dict:
    return {
        "event_name": event_name,
        "occurred_at": timezone.now().isoformat(),
        "anonymous_id": str(uuid.uuid4()),
        **extra,
    }


def test_analytics_serializer_rejects_each_forbidden_pii_key():
    """Cada chave de FORBIDDEN_PII_KEYS é rejeitada individualmente no campo properties."""
    for key in FORBIDDEN_PII_KEYS:
        data = _base_event(properties={key: "valor-sensivel"})
        serializer = AnalyticsEventInputSerializer(data=data)
        assert not serializer.is_valid(), (
            f"Chave PII '{key}' foi aceita indevidamente no campo properties."
        )
        assert "properties" in serializer.errors


def test_analytics_serializer_accepts_safe_properties():
    """Propriedades sem PII e com evento válido passam na validação."""
    safe_data = _base_event(
        event_name="route_viewed",
        properties={"source": "card", "offline_capable": "true"},
    )
    serializer = AnalyticsEventInputSerializer(data=safe_data)
    assert serializer.is_valid(), (
        f"Propriedades seguras foram rejeitadas indevidamente: {serializer.errors}"
    )


def test_analytics_serializer_rejects_unknown_event_name():
    """Nomes de evento fora de ALLOWED_EVENTS são rejeitados pelo serializer."""
    data = _base_event(event_name="evento_arbitrario_nao_permitido")
    serializer = AnalyticsEventInputSerializer(data=data)
    assert not serializer.is_valid()
    assert "event_name" in serializer.errors


def test_analytics_allowed_events_covers_key_user_actions():
    """ALLOWED_EVENTS inclui os eventos mínimos exigidos pela plataforma."""
    mandatory = {
        "app_opened",
        "screen_viewed",
        "route_viewed",
        "offline_download_started",
        "consent_changed",
    }
    missing = mandatory - ALLOWED_EVENTS
    assert not missing, f"Eventos obrigatórios ausentes de ALLOWED_EVENTS: {missing}"


def test_analytics_forbidden_pii_keys_covers_critical_identifiers():
    """FORBIDDEN_PII_KEYS protege pelo menos os identificadores pessoais críticos."""
    critical = {"email", "cpf", "phone", "user_id", "latitude", "longitude"}
    missing = critical - FORBIDDEN_PII_KEYS
    assert not missing, f"Identificadores críticos ausentes de FORBIDDEN_PII_KEYS: {missing}"


@pytest.mark.django_db
def test_seed_multiregion_preserves_published_status():
    """seed_multiregion_pilot não altera o status PUBLISHED
    nem rebaixa para DRAFT em execuções normais.
    """
    from django.core.management import call_command

    from modules.core.models import EditorialStatus
    from modules.regions.models import Region
    from modules.routes.models import Route

    call_command("seed_multiregion_pilot", publish_demo=True)
    region = Region.objects.get(slug="santarem-alter-do-chao")
    route = Route.objects.get(region=region, slug="orla-alter-do-chao")
    assert region.status == EditorialStatus.PUBLISHED
    assert route.editorial_status == EditorialStatus.PUBLISHED

    # Executa novamente sem --publish-demo; deve preservar o status PUBLISHED existente
    call_command("seed_multiregion_pilot")
    region.refresh_from_db()
    route.refresh_from_db()
    assert region.status == EditorialStatus.PUBLISHED, "Região foi rebaixada indevidamente no seed!"
    assert route.editorial_status == EditorialStatus.PUBLISHED, (
        "Rota foi rebaixada indevidamente no seed!"
    )
