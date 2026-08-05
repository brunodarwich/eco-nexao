import uuid
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory

from modules.accounts.permissions import AdminRole
from modules.analytics.models import DailyAnalyticsAggregate, RawAnalyticsEvent
from modules.analytics.serializers import AnalyticsEventInputSerializer
from modules.analytics.views import admin_analytics_summary


def test_analytics_serializer_valid():
    data = {
        "event_name": "app_opened",
        "occurred_at": timezone.now().isoformat(),
        "anonymous_id": str(uuid.uuid4()),
        "properties": {"entry_type": "direct"},
    }
    serializer = AnalyticsEventInputSerializer(data=data)
    assert serializer.is_valid(), serializer.errors


def test_analytics_serializer_invalid_event():
    data = {
        "event_name": "invalid_tracking_event",
        "occurred_at": timezone.now().isoformat(),
        "anonymous_id": str(uuid.uuid4()),
    }
    serializer = AnalyticsEventInputSerializer(data=data)
    assert not serializer.is_valid()
    assert "event_name" in serializer.errors


def test_analytics_serializer_forbidden_pii():
    data = {
        "event_name": "screen_viewed",
        "occurred_at": timezone.now().isoformat(),
        "anonymous_id": str(uuid.uuid4()),
        "properties": {"email": "user@example.com"},
    }
    serializer = AnalyticsEventInputSerializer(data=data)
    assert not serializer.is_valid()


def test_analytics_serializer_undeclared_property_rejected():
    data = {
        "event_name": "app_opened",
        "occurred_at": timezone.now().isoformat(),
        "anonymous_id": str(uuid.uuid4()),
        "properties": {"entry_type": "direct", "unexpected_param": 123},
    }
    serializer = AnalyticsEventInputSerializer(data=data)
    assert not serializer.is_valid()
    assert "properties" in serializer.errors


def test_analytics_serializer_invalid_property_enum_rejected():
    data = {
        "event_name": "app_opened",
        "occurred_at": timezone.now().isoformat(),
        "anonymous_id": str(uuid.uuid4()),
        "properties": {"entry_type": "invalid_shortcut"},
    }
    serializer = AnalyticsEventInputSerializer(data=data)
    assert not serializer.is_valid()
    assert "properties" in serializer.errors


def test_analytics_serializer_future_and_old_timestamp_rejected():
    # Futuro (+10 min)
    future_data = {
        "event_name": "app_opened",
        "occurred_at": (timezone.now() + timedelta(minutes=10)).isoformat(),
        "anonymous_id": str(uuid.uuid4()),
        "properties": {"entry_type": "direct"},
    }
    serializer = AnalyticsEventInputSerializer(data=future_data)
    assert not serializer.is_valid()
    assert "occurred_at" in serializer.errors

    # Passado antigo (-100 dias)
    old_data = {
        "event_name": "app_opened",
        "occurred_at": (timezone.now() - timedelta(days=100)).isoformat(),
        "anonymous_id": str(uuid.uuid4()),
        "properties": {"entry_type": "direct"},
    }
    serializer_old = AnalyticsEventInputSerializer(data=old_data)
    assert not serializer_old.is_valid()
    assert "occurred_at" in serializer_old.errors


def test_analytics_serializer_recursive_pii_and_free_text_rejected():
    data = {
        "event_name": "app_opened",
        "occurred_at": timezone.now().isoformat(),
        "anonymous_id": str(uuid.uuid4()),
        "properties": {
            "entry_type": "direct",
            "nested": {"contact_email": "usuario@exemplo.org"},
        },
    }
    serializer = AnalyticsEventInputSerializer(data=data)
    assert not serializer.is_valid()


@pytest.mark.django_db
def test_public_event_batch_atomic_aggregation_db():
    api_client = APIClient()
    today = timezone.localdate()
    anonymous_id = str(uuid.uuid4())

    payload = {
        "events": [
            {
                "event_name": "app_opened",
                "occurred_at": timezone.now().isoformat(),
                "anonymous_id": anonymous_id,
                "region_id": "santarem-alter-do-chao",
                "route_id": "pindobal",
                "properties": {"entry_type": "direct"},
            },
            {
                "event_name": "app_opened",
                "occurred_at": timezone.now().isoformat(),
                "anonymous_id": anonymous_id,
                "region_id": "santarem-alter-do-chao",
                "route_id": "pindobal",
                "properties": {"entry_type": "link"},
            },
        ]
    }

    res = api_client.post("/api/v1/events/batch", payload, format="json")
    assert res.status_code == 201
    assert res.data["received"] == 2

    assert RawAnalyticsEvent.objects.count() == 2
    agg = DailyAnalyticsAggregate.objects.get(
        date=today,
        event_name="app_opened",
        region_slug="santarem-alter-do-chao",
        route_slug="pindobal",
    )
    assert agg.count == 2


def test_admin_analytics_summary_view():
    factory = APIRequestFactory()
    mock_item = DailyAnalyticsAggregate(
        date=timezone.now().date(),
        event_name="route_viewed",
        region_slug="santarem-alter-do-chao",
        route_slug="pindobal",
        count=15,
    )
    mock_qs = [mock_item]

    request = factory.get("/api/v1/admin/analytics/summary?region_slug=santarem-alter-do-chao")
    request.user = APIClient()
    request.user.is_authenticated = True
    request.user.is_active = True
    request.user.is_staff = True

    class DummyQS:
        def order_by(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def aggregate(self, *args, **kwargs):
            return {"total": 15}

        def __getitem__(self, item):
            return mock_qs

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mp.setattr("modules.analytics.views.has_admin_action", lambda user, action: True)
        mp.setattr(
            "modules.analytics.views.get_user_roles",
            lambda user: frozenset({AdminRole.ADMINISTRATOR}),
        )
        mp.setattr("modules.analytics.views.DailyAnalyticsAggregate.objects.all", lambda: DummyQS())
        response = admin_analytics_summary(request)

    assert response.status_code == 200
    assert response.data["total_events"] == 15
    assert len(response.data["aggregates"]) == 1
    assert response.data["aggregates"][0]["count"] == 15


@pytest.mark.django_db
def test_public_event_batch_throttling_and_independent_limits():
    api_client = APIClient()
    from modules.core.models import EditorialStatus
    from modules.regions.models import Region
    from modules.routes.models import Route

    cache.clear()

    region = Region.objects.create(
        public_name="Tapajós",
        slug="tapajos",
        center_point="POINT(-54.7 -2.4)",
        status=EditorialStatus.PUBLISHED,
    )
    Route.objects.create(
        region=region,
        slug="pindobal",
        public_name="Pindobal",
        short_promise="Promessa",
        duration_minutes=60,
        difficulty="easy",
        editorial_status=EditorialStatus.PUBLISHED,
    )

    analytics_payload = {
        "events": [
            {
                "event_name": "app_opened",
                "occurred_at": timezone.now().isoformat(),
                "anonymous_id": str(uuid.uuid4()),
                "properties": {"entry_type": "direct"},
            }
        ]
    }

    report_payload = {
        "description": "Relato para testar escopo independente.",
        "region_slug": "tapajos",
        "report_type": "incorrect_info",
        "reporter_contact": "scope@exemplo.org",
        "target_slug": "pindobal",
        "target_type": "route",
    }

    custom_rates = {
        **settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {}),
        "analytics_batch": "3/hour",
        "public_reports": "2/hour",
    }

    with patch.dict(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], custom_rates):
        initial_raw_count = RawAnalyticsEvent.objects.count()

        # 3 envios permitidos em analytics
        for i in range(3):
            res = api_client.post("/api/v1/events/batch", analytics_payload, format="json")
            assert res.status_code == 201, f"Analytics falhou na tentativa {i + 1}"

        # 4º envio de analytics deve ser bloqueado com 429
        blocked_analytics = api_client.post(
            "/api/v1/events/batch", analytics_payload, format="json"
        )
        assert blocked_analytics.status_code == 429
        assert "detail" in blocked_analytics.data

        # Verificar não-persistência do lote bloqueado
        assert RawAnalyticsEvent.objects.count() == initial_raw_count + 3

        # Demonstrar escopos independentes: public_reports ainda deve permitir
        # envios dentro de seu limite
        report_res = api_client.post("/api/v1/public/reports/", report_payload, format="json")
        assert report_res.status_code == 201


@pytest.mark.django_db
def test_purge_analytics_command_dry_run_and_execution():
    now = timezone.now()
    old_event = RawAnalyticsEvent.objects.create(
        event_name="app_opened",
        occurred_at=now - timedelta(days=100),
        anonymous_id=str(uuid.uuid4()),
    )
    recent_event = RawAnalyticsEvent.objects.create(
        event_name="app_opened",
        occurred_at=now - timedelta(days=10),
        anonymous_id=str(uuid.uuid4()),
    )

    # 1. Testar modo dry-run (não exclui nada)
    out_dry = StringIO()
    call_command("purge_analytics", "--days=90", "--dry-run", stdout=out_dry)
    output_dry = out_dry.getvalue()
    assert "[PRÉVIA]" in output_dry
    assert "1 evento(s)" in output_dry
    assert RawAnalyticsEvent.objects.count() == 2

    # 2. Testar expurgo real
    out_real = StringIO()
    call_command("purge_analytics", "--days=90", stdout=out_real)
    output_real = out_real.getvalue()
    assert "[EXPURGO]" in output_real
    assert "1 evento(s)" in output_real
    assert RawAnalyticsEvent.objects.count() == 1
    assert RawAnalyticsEvent.objects.filter(event_id=recent_event.event_id).exists()
    assert not RawAnalyticsEvent.objects.filter(event_id=old_event.event_id).exists()
