import uuid
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from config.openapi_validator import assert_response_matches_openapi
from modules.accounts.models import AdministrativeRegionScope
from modules.accounts.permissions import ROLE_GROUP_PREFIX, AdminRole
from modules.analytics.models import DailyAnalyticsAggregate, RawAnalyticsEvent
from modules.analytics.serializers import AnalyticsEventInputSerializer
from modules.catalog.models import Actor, Category, RouteActor
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Route

User = get_user_model()


@pytest.fixture
def analytics_domain(db):
    region = Region.objects.create(
        public_name="Tapajós",
        slug="tapajos",
        center_point="POINT(-54.7 -2.4)",
        status=EditorialStatus.PUBLISHED,
    )
    other_region = Region.objects.create(
        public_name="Xingu",
        slug="xingu",
        center_point="POINT(-52 -3)",
        status=EditorialStatus.PUBLISHED,
    )
    route = Route.objects.create(
        region=region,
        slug="pindobal",
        public_name="Pindobal",
        short_promise="Visita responsável",
        duration_minutes=60,
        difficulty=Route.Difficulty.EASY,
        editorial_status=EditorialStatus.PUBLISHED,
    )
    category = Category.objects.create(slug="apoio", public_name="Apoio")
    actor = Actor.objects.create(
        external_id="actor-analytics",
        actor_kind=Actor.ActorKind.SUPPORT,
        category=category,
        slug="base-pindobal",
        public_name="Base Pindobal",
        short_description="Apoio local",
        editorial_status=EditorialStatus.PUBLISHED,
    )
    RouteActor.objects.create(
        route=route,
        actor=actor,
        route_role=RouteActor.RouteRole.SUPPORT,
    )
    analyst_group, _ = Group.objects.get_or_create(name=f"{ROLE_GROUP_PREFIX}{AdminRole.ANALYST}")
    analyst = User.objects.create_user(username="analyst", is_staff=True)
    analyst.groups.add(analyst_group)
    AdministrativeRegionScope.objects.create(user=analyst, region=region)
    return {
        "region": region,
        "other_region": other_region,
        "route": route,
        "actor": actor,
        "analyst": analyst,
    }


def event_payload(event_name="session_opened", **extra):
    return {
        "event_id": str(uuid.uuid4()),
        "event_name": event_name,
        "occurred_at": timezone.now().isoformat(),
        "region_id": "tapajos",
        **extra,
    }


def test_allowlist_accepts_only_minimal_dimensions():
    serializer = AnalyticsEventInputSerializer(data=event_payload())
    assert serializer.is_valid(), serializer.errors

    for forbidden in (
        {"latitude": -2.4},
        {"coordinates": [-54.7, -2.4]},
        {"email": "visitor@example.org"},
        {"message": "texto livre"},
        {"anonymous_id": str(uuid.uuid4())},
        {"session_id": str(uuid.uuid4())},
        {"properties": {"anything": "value"}},
    ):
        blocked = AnalyticsEventInputSerializer(data={**event_payload(), **forbidden})
        assert not blocked.is_valid(), forbidden


@pytest.mark.django_db
def test_batch_requires_consent_and_rejects_unknown_domain(analytics_domain):
    client = APIClient()
    denied = client.post(
        "/api/v1/events/batch",
        {"consent_granted": False, "events": [event_payload()]},
        format="json",
    )
    assert denied.status_code == 400
    unknown = client.post(
        "/api/v1/events/batch",
        {
            "consent_granted": True,
            "events": [event_payload(region_id="regiao-inexistente")],
        },
        format="json",
    )
    assert unknown.status_code == 400
    assert RawAnalyticsEvent.objects.count() == 0


@pytest.mark.django_db
def test_batch_is_atomic_and_uses_single_non_nullable_aggregate(analytics_domain):
    client = APIClient()
    events = [event_payload(), event_payload()]
    response = client.post(
        "/api/v1/events/batch",
        {"consent_granted": True, "events": events},
        format="json",
    )
    assert response.status_code == 201
    aggregate = DailyAnalyticsAggregate.objects.get(event_name="session_opened")
    assert aggregate.support_point_id == ""
    assert aggregate.count == 2
    assert (
        RawAnalyticsEvent.objects.filter(
            anonymous_id__isnull=True,
            session_id__isnull=True,
            consent_id__isnull=True,
        ).count()
        == 2
    )

    invalid_batch = client.post(
        "/api/v1/events/batch",
        {
            "consent_granted": True,
            "events": [
                event_payload(),
                event_payload("route_opened", route_id="rota-inexistente"),
            ],
        },
        format="json",
    )
    assert invalid_batch.status_code == 400
    aggregate.refresh_from_db()
    assert aggregate.count == 2
    assert RawAnalyticsEvent.objects.count() == 2


@pytest.mark.django_db
def test_contact_dimension_and_operational_privacy_threshold(analytics_domain):
    actor_id = str(analytics_domain["actor"].id)
    DailyAnalyticsAggregate.objects.create(
        date=timezone.localdate(),
        event_name="contact_opened",
        region_slug="tapajos",
        route_slug="pindobal",
        support_point_id=actor_id,
        count=12,
    )
    DailyAnalyticsAggregate.objects.create(
        date=timezone.localdate(),
        event_name="route_opened",
        region_slug="tapajos",
        route_slug="pindobal",
        count=9,
    )
    client = APIClient()
    client.force_authenticate(analytics_domain["analyst"])
    response = client.get(
        "/api/v1/admin/analytics/operational?region_slug=tapajos&route_slug=pindobal"
    )
    assert response.status_code == 200
    metrics = {item["event_name"]: item for item in response.data["metrics"]}
    assert metrics["contact_opened"]["count"] == 12
    assert metrics["route_opened"] == {
        "event_name": "route_opened",
        "count": None,
        "suppressed": True,
    }
    assert response.data["ranking"] == [
        {
            "support_point_id": actor_id,
            "support_point_name": "Base Pindobal",
            "contacts": 12,
        }
    ]
    assert response["Cache-Control"] == "no-store"
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_operational_analytics_auth_scope_and_empty_region(analytics_domain):
    client = APIClient()
    unauthenticated = client.get("/api/v1/admin/analytics/operational?region_slug=tapajos")
    assert unauthenticated.status_code in (401, 403)
    client.force_authenticate(analytics_domain["analyst"])
    forbidden = client.get("/api/v1/admin/analytics/operational?region_slug=xingu")
    assert forbidden.status_code == 403
    empty = client.get("/api/v1/admin/analytics/operational?region_slug=tapajos")
    assert empty.status_code == 200
    assert empty.data["ranking"] == []


@pytest.mark.django_db
def test_analytics_throttle_does_not_persist_blocked_batch(analytics_domain):
    cache.clear()
    client = APIClient()
    rates = {
        **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
        "analytics_batch": "1/hour",
    }
    with patch.dict(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], rates):
        payload = {"consent_granted": True, "events": [event_payload()]}
        assert client.post("/api/v1/events/batch", payload, format="json").status_code == 201
        payload["events"] = [event_payload()]
        assert client.post("/api/v1/events/batch", payload, format="json").status_code == 429
    assert RawAnalyticsEvent.objects.count() == 1


@pytest.mark.django_db
def test_purge_removes_raw_after_24h_and_aggregates_after_13_months():
    now = timezone.now()
    old_event = RawAnalyticsEvent.objects.create(
        event_name="session_opened",
        occurred_at=now - timedelta(hours=25),
        region_id="tapajos",
    )
    recent_event = RawAnalyticsEvent.objects.create(
        event_name="session_opened",
        occurred_at=now - timedelta(hours=23),
        region_id="tapajos",
    )
    old_aggregate = DailyAnalyticsAggregate.objects.create(
        date=(now - timedelta(days=397)).date(),
        event_name="session_opened",
        region_slug="tapajos",
    )
    output = StringIO()
    call_command("purge_analytics", "--hours=24", "--dry-run", stdout=output)
    assert RawAnalyticsEvent.objects.count() == 2
    call_command("purge_analytics", "--hours=24", stdout=output)
    assert not RawAnalyticsEvent.objects.filter(pk=old_event.pk).exists()
    assert RawAnalyticsEvent.objects.filter(pk=recent_event.pk).exists()
    assert not DailyAnalyticsAggregate.objects.filter(pk=old_aggregate.pk).exists()
