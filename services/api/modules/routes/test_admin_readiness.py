from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.gis.geos import LineString, Point
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from config.openapi_validator import assert_response_matches_openapi
from modules.accounts.models import AdministrativeRegionScope
from modules.accounts.permissions import ROLE_GROUP_PREFIX, AdminRole
from modules.catalog.models import Actor, Category, ContactChannel, RouteActor
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Alert, Route, RouteSegment, RouteStage
from modules.routes.readiness import READINESS_WEIGHTS, calculate_route_readiness

User = get_user_model()


@pytest.fixture
def readiness_domain(db):
    region = Region.objects.create(
        public_name="Tapajós",
        slug="tapajos",
        center_point=Point(-54.7, -2.4, srid=4326),
        status=EditorialStatus.PUBLISHED,
    )
    other_region = Region.objects.create(
        public_name="Xingu",
        slug="xingu",
        center_point=Point(-52, -3, srid=4326),
        status=EditorialStatus.PUBLISHED,
    )
    route = Route.objects.create(
        region=region,
        slug="rota-pronta",
        public_name="Rota Pronta",
        short_promise="Experiência responsável",
        description="Descrição editorial completa.",
        duration_minutes=90,
        difficulty=Route.Difficulty.EASY,
        transport_modes=["walking"],
        preparation_content="Leve água.",
        offline_enabled=True,
        editorial_status=EditorialStatus.REVIEW,
    )
    start = RouteStage.objects.create(
        route=route,
        position=1,
        public_name="Início",
        point=Point(-54.7, -2.4, srid=4326),
        stage_type=RouteStage.StageType.START,
    )
    end = RouteStage.objects.create(
        route=route,
        position=2,
        public_name="Fim",
        point=Point(-54.71, -2.41, srid=4326),
        stage_type=RouteStage.StageType.END,
    )
    RouteSegment.objects.create(
        route=route,
        from_stage=start,
        to_stage=end,
        geometry=LineString(start.point, end.point, srid=4326),
        transport_mode="walking",
        distance_meters=1000,
        duration_minutes=20,
    )
    category = Category.objects.create(slug="apoio-ready", public_name="Apoio")
    actor = Actor.objects.create(
        external_id="ready-actor",
        actor_kind=Actor.ActorKind.SUPPORT,
        category=category,
        slug="base-ready",
        public_name="Base verificada",
        short_description="Apoio",
        editorial_status=EditorialStatus.PUBLISHED,
    )
    RouteActor.objects.create(
        route=route,
        actor=actor,
        route_role=RouteActor.RouteRole.SUPPORT,
    )
    ContactChannel.objects.create(
        actor=actor,
        channel_type=ContactChannel.ChannelType.WEBSITE,
        public_value="https://example.org",
        is_public=True,
        source_type=ContactChannel.SourceType.OTHER_PUBLIC,
        source_reference="Fonte pública",
        verified_at=timezone.now(),
    )
    analyst_group, _ = Group.objects.get_or_create(name=f"{ROLE_GROUP_PREFIX}{AdminRole.ANALYST}")
    analyst = User.objects.create_user(username="route-analyst", is_staff=True)
    analyst.groups.add(analyst_group)
    AdministrativeRegionScope.objects.create(user=analyst, region=region)
    return {"region": region, "other_region": other_region, "route": route, "analyst": analyst}


@pytest.mark.django_db
def test_formula_is_versioned_weighted_and_ready(readiness_domain):
    result = calculate_route_readiness(readiness_domain["route"]).payload
    assert result["weights"] == READINESS_WEIGHTS
    assert result["dimensions"] == {
        "content": 100,
        "trace": 100,
        "catalog": 100,
        "alerts": 100,
        "offline": 100,
    }
    assert result["score"] == 100
    assert result["is_ready"] is True
    assert result["verified_contacts_count"] == 1
    assert result["blocking_reasons"] == []


@pytest.mark.django_db
def test_formula_reports_mandatory_blockers_and_editorial_states(readiness_domain):
    route = readiness_domain["route"]
    route.description = ""
    route.preparation_content = ""
    route.offline_enabled = False
    route.editorial_status = EditorialStatus.DRAFT
    route.save()
    Alert.objects.create(
        region=route.region,
        route=route,
        severity=Alert.Severity.CRITICAL,
        title="Interdição",
        description="Trecho interditado",
        starts_at=timezone.now() - timedelta(hours=1),
        status=EditorialStatus.PUBLISHED,
    )
    result = calculate_route_readiness(route).payload
    assert result["editorial_status"] == EditorialStatus.DRAFT
    assert result["is_ready"] is False
    assert "missing_required_field:description" in result["blocking_reasons"]
    assert "active_critical_alert" in result["blocking_reasons"]
    assert result["score"] == 66


@pytest.mark.django_db
def test_readiness_endpoint_scope_empty_and_openapi(readiness_domain):
    client = APIClient()
    assert client.get("/api/v1/admin/routes/readiness?region_slug=tapajos").status_code in (
        401,
        403,
    )
    client.force_authenticate(readiness_domain["analyst"])
    forbidden = client.get("/api/v1/admin/routes/readiness?region_slug=xingu")
    assert forbidden.status_code == 403
    response = client.get("/api/v1/admin/routes/readiness?region_slug=tapajos")
    assert response.status_code == 200
    assert response.data["routes"][0]["editorial_status"] == "review"
    assert response.data["routes"][0]["published_version"] is None
    assert_response_matches_openapi(response, expected_status=200)

    admin_group, _ = Group.objects.get_or_create(
        name=f"{ROLE_GROUP_PREFIX}{AdminRole.ADMINISTRATOR}"
    )
    administrator = User.objects.create_user(username="readiness-admin", is_staff=True)
    administrator.groups.add(admin_group)
    client.force_authenticate(administrator)
    empty = client.get("/api/v1/admin/routes/readiness?region_slug=xingu")
    assert empty.status_code == 200
    assert empty.data == {"region_slug": "xingu", "routes": []}


@pytest.mark.django_db
def test_readiness_endpoint_throttle(readiness_domain):
    cache.clear()
    client = APIClient()
    client.force_authenticate(readiness_domain["analyst"])
    rates = {
        **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
        "admin_readiness": "1/hour",
    }
    with patch.dict(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], rates):
        assert client.get("/api/v1/admin/routes/readiness?region_slug=tapajos").status_code == 200
        assert client.get("/api/v1/admin/routes/readiness?region_slug=tapajos").status_code == 429
