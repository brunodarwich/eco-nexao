"""Checklist editorial, acessível, offline e analítico — Tarefa 12.3.

Verifica que os contratos de dados das rotas satisfazem os requisitos
de publicação, acessibilidade, disponibilidade offline e conformidade
LGPD dos eventos de analytics.

Não requer banco de dados: testa contratos de serialização, filtros de
queryset e allowlists de campos declarados nas views e serializers.

_Requisitos: RF-01 a RF-13, RNF-01 a RNF-08_
"""

import pytest
from django.utils import timezone

from modules.analytics.serializers import (
    ALLOWED_EVENTS,
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
def _base_event(event_name: str = "session_opened", **extra) -> dict:
    return {
        "event_id": "00000000-0000-4000-8000-000000000001",
        "event_name": event_name,
        "occurred_at": timezone.now().isoformat(),
        "region_id": "tapajos",
        **extra,
    }


def test_analytics_serializer_rejects_each_forbidden_pii_key():
    """Identificadores e coordenadas são rejeitados no envelope do evento."""
    for key in ("email", "phone", "user_id", "session_id", "latitude", "longitude"):
        data = _base_event(**{key: "valor-sensivel"})
        serializer = AnalyticsEventInputSerializer(data=data)
        assert not serializer.is_valid(), f"Chave PII '{key}' foi aceita indevidamente."


def test_analytics_serializer_accepts_safe_properties():
    """Somente dimensões declaradas para o evento passam na validação."""
    safe_data = _base_event(
        event_name="route_opened",
        route_id="pindobal",
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
        "session_opened",
        "route_opened",
        "contact_opened",
        "offline_download_completed",
    }
    missing = mandatory - ALLOWED_EVENTS
    assert not missing, f"Eventos obrigatórios ausentes de ALLOWED_EVENTS: {missing}"


def test_analytics_allowlist_excludes_personal_identifiers():
    serializer = AnalyticsEventInputSerializer()
    for forbidden in ("anonymous_id", "session_id", "consent_id", "properties"):
        assert forbidden not in serializer.fields


@pytest.mark.django_db
def test_seed_multiregion_creates_drafts_and_preserves_published_status():
    """O seed nunca publica e não rebaixa conteúdo publicado pelo workflow."""
    from django.core.management import call_command

    from modules.core.models import EditorialStatus
    from modules.regions.models import Region
    from modules.routes.models import Route

    call_command("seed_multiregion_pilot")
    region = Region.objects.get(slug="santarem-alter-do-chao")
    route = Route.objects.get(region=region, slug="orla-alter-do-chao")
    assert region.status == EditorialStatus.DRAFT
    assert route.editorial_status == EditorialStatus.DRAFT

    region.status = EditorialStatus.PUBLISHED
    region.published_version = 7
    region.save(update_fields=["status", "published_version"])
    route.editorial_status = EditorialStatus.PUBLISHED
    route.save(update_fields=["editorial_status"])

    # Executa novamente; deve preservar o status PUBLISHED existente.
    call_command("seed_multiregion_pilot")
    region.refresh_from_db()
    route.refresh_from_db()
    assert region.status == EditorialStatus.PUBLISHED, "Região foi rebaixada indevidamente no seed!"
    assert route.editorial_status == EditorialStatus.PUBLISHED, (
        "Rota foi rebaixada indevidamente no seed!"
    )
    assert region.published_version == 7


@pytest.mark.django_db
def test_seed_pindobal_never_publishes_and_preserves_workflow_state():
    from django.core.management import call_command

    from modules.catalog.models import Actor
    from modules.core.models import EditorialStatus
    from modules.regions.models import Region
    from modules.routes.models import Alert, Route

    call_command("seed_pindobal_demo")
    region = Region.objects.get(slug="santarem-alter-do-chao")
    route = Route.objects.get(region=region, slug="pindobal")
    alert = Alert.objects.get(route=route, title="Informações demonstrativas")
    actor = Actor.objects.get(external_id="demo:pindobal:apoio")

    assert region.status == EditorialStatus.DRAFT
    assert route.editorial_status == EditorialStatus.DRAFT
    assert alert.status == EditorialStatus.DRAFT
    assert actor.editorial_status == EditorialStatus.DRAFT

    region.status = EditorialStatus.PUBLISHED
    region.published_version = 9
    region.save(update_fields=["status", "published_version"])
    route.editorial_status = EditorialStatus.PUBLISHED
    route.save(update_fields=["editorial_status"])
    alert.status = EditorialStatus.PUBLISHED
    alert.save(update_fields=["status"])
    actor.editorial_status = EditorialStatus.PUBLISHED
    actor.save(update_fields=["editorial_status"])

    call_command("seed_pindobal_demo")
    region.refresh_from_db()
    route.refresh_from_db()
    alert.refresh_from_db()
    actor.refresh_from_db()

    assert region.status == EditorialStatus.PUBLISHED
    assert region.published_version == 9
    assert route.editorial_status == EditorialStatus.PUBLISHED
    assert alert.status == EditorialStatus.PUBLISHED
    assert actor.editorial_status == EditorialStatus.PUBLISHED
