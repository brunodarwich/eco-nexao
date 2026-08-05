import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from config.openapi_validator import assert_response_matches_openapi
from modules.accounts.models import AdministrativeRegionScope
from modules.accounts.permissions import ROLE_GROUP_PREFIX, AdminRole
from modules.catalog.admin_throttles import SupportPointCreateUserThrottle
from modules.catalog.models import Category
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.reports.models import PublicReport
from modules.routes.models import Route, RouteStage

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_domain(db):
    boundary = MultiPolygon(
        Polygon(
            (
                (-55.2, -2.8),
                (-54.7, -2.8),
                (-54.7, -2.2),
                (-55.2, -2.2),
                (-55.2, -2.8),
            )
        ),
        srid=4326,
    )
    region = Region.objects.create(
        public_name="Alter do Chão",
        slug="alter-do-chao",
        center_point="POINT(-54.95 -2.50)",
        boundary=boundary,
        status=EditorialStatus.PUBLISHED,
    )
    route = Route.objects.create(
        region=region,
        public_name="Rota Pindobal",
        slug="rota-pindobal",
        short_promise="Promessa de teste",
        duration_minutes=60,
        difficulty="easy",
        editorial_status=EditorialStatus.PUBLISHED,
    )
    stage = RouteStage.objects.create(
        route=route,
        position=1,
        public_name="Início",
        point="POINT(-54.96 -2.51)",
        stage_type=RouteStage.StageType.START,
    )
    category = Category.objects.create(
        slug="apoio-teste",
        public_name="Apoio teste",
        is_active=True,
    )
    report = PublicReport.objects.create(
        region_slug="alter-do-chao",
        target_type=PublicReport.TargetType.ROUTE,
        target_id=str(route.id),
        target_slug="rota-pindobal",
        report_type=PublicReport.ReportType.INCORRECT_INFO,
        description="Descrição detalhada do relato de teste.",
        reporter_contact="visitante@exemplo.org",
        status=PublicReport.Status.PENDING,
    )
    return {
        "region": region,
        "route": route,
        "stage": stage,
        "category": category,
        "report": report,
    }


def support_point_payload(test_domain, *, suffix=""):
    return {
        "actor": {
            "category_id": str(test_domain["category"].pk),
            "public_name": f"Base administrativa{suffix}",
            "short_description": "Ponto conferido pela equipe editorial.",
        },
        "location": {
            "label": "Principal",
            "address_fields": {"locality": f"Local teste{suffix}", "country_code": "BR"},
            "latitude": -2.497,
            "longitude": -54.952,
            "public_visibility": True,
        },
        "contacts": [],
        "route_links": [
            {
                "route_id": str(test_domain["route"].pk),
                "stage_id": str(test_domain["stage"].pk),
                "route_role": "support",
                "editorial_position": 1,
                "is_featured": False,
                "sponsorship_label": "",
            }
        ],
    }


@pytest.fixture
def admin_user(db, test_domain):
    user = User.objects.create_user(
        username="admin_test", email="admin@exemplo.org", password="password123", is_staff=True
    )
    group, _ = Group.objects.get_or_create(name=f"{ROLE_GROUP_PREFIX}{AdminRole.ADMINISTRATOR}")
    user.groups.add(group)
    AdministrativeRegionScope.objects.create(user=user, region=test_domain["region"])
    return user


@pytest.fixture
def unauthorized_user(db):
    return User.objects.create_user(
        username="unauthorized_test", email="noadmin@exemplo.org", password="password123"
    )


@pytest.mark.django_db
def test_openapi_health_200(api_client):
    response = api_client.get("/api/v1/health")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_regions_list_200(api_client, test_domain):
    response = api_client.get("/api/v1/regions")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_routes_list_200(api_client, test_domain):
    response = api_client.get("/api/v1/regions/alter-do-chao/routes")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_route_detail_200(api_client, test_domain):
    response = api_client.get("/api/v1/regions/alter-do-chao/routes/rota-pindobal")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_route_catalog_200(api_client, test_domain):
    response = api_client.get("/api/v1/regions/alter-do-chao/routes/rota-pindobal/catalog")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_admin_csrf_200(api_client):
    response = api_client.get("/api/v1/admin/auth/csrf")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_admin_session_200(api_client):
    response = api_client.get("/api/v1/admin/auth/session")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_admin_login_success_200(api_client, admin_user):
    login_res = api_client.post(
        "/api/v1/admin/auth/login",
        data={"username": "admin_test", "password": "password123"},
        format="json",
    )
    assert_response_matches_openapi(login_res, expected_status=200)

    logout_res = api_client.post("/api/v1/admin/auth/logout")
    assert_response_matches_openapi(logout_res, expected_status=200)


@pytest.mark.django_db
def test_openapi_admin_login_invalid_credentials_401(api_client):
    response = api_client.post(
        "/api/v1/admin/auth/login",
        data={"username": "admin_test", "password": "wrongpassword"},
        format="json",
    )
    assert_response_matches_openapi(response, expected_status=401)


@pytest.mark.django_db
def test_openapi_support_point_create_real_201(api_client, admin_user, test_domain):
    api_client.force_login(admin_user)
    response = api_client.post(
        "/api/v1/admin/catalog/support-points/",
        data=support_point_payload(test_domain),
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert response.json()["editorial_status"] == "draft"
    assert response.json()["actor_kind"] == "support"
    assert_response_matches_openapi(response, expected_status=201)


@pytest.mark.django_db
def test_openapi_support_point_create_real_400(api_client, admin_user, test_domain):
    api_client.force_login(admin_user)
    response = api_client.post(
        "/api/v1/admin/catalog/support-points/",
        data=support_point_payload(test_domain),
        format="json",
        HTTP_IDEMPOTENCY_KEY="not-a-uuid",
    )

    assert_response_matches_openapi(response, expected_status=400)


@pytest.mark.django_db
def test_openapi_support_point_create_real_401(api_client, test_domain):
    response = api_client.post(
        "/api/v1/admin/catalog/support-points/",
        data=support_point_payload(test_domain),
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert_response_matches_openapi(response, expected_status=401)


@pytest.mark.django_db
def test_openapi_support_point_create_real_403(api_client, unauthorized_user, test_domain):
    unauthorized_user.is_staff = True
    unauthorized_user.save(update_fields=["is_staff"])
    api_client.force_login(unauthorized_user)
    response = api_client.post(
        "/api/v1/admin/catalog/support-points/",
        data=support_point_payload(test_domain),
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_support_point_create_real_409(api_client, admin_user, test_domain):
    api_client.force_login(admin_user)
    payload = support_point_payload(test_domain)
    first = api_client.post(
        "/api/v1/admin/catalog/support-points/",
        data=payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert first.status_code == 201
    response = api_client.post(
        "/api/v1/admin/catalog/support-points/",
        data=payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert_response_matches_openapi(response, expected_status=409)


@pytest.mark.django_db
def test_openapi_support_point_create_real_500(api_client, admin_user, test_domain):
    api_client.force_login(admin_user)
    with patch(
        "modules.catalog.support_point_views.create_support_point",
        side_effect=RuntimeError("database detail must not leak"),
    ):
        response = api_client.post(
            "/api/v1/admin/catalog/support-points/",
            data=support_point_payload(test_domain, suffix=" 500"),
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )

    assert "database detail" not in response.content.decode()
    assert_response_matches_openapi(response, expected_status=500)


@pytest.mark.django_db
def test_openapi_support_point_create_real_429(api_client, admin_user, test_domain):
    cache.clear()
    api_client.force_login(admin_user)
    with patch.object(SupportPointCreateUserThrottle, "get_rate", return_value="1/hour"):
        first = api_client.post(
            "/api/v1/admin/catalog/support-points/",
            data=support_point_payload(test_domain, suffix=" throttle-a"),
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        response = api_client.post(
            "/api/v1/admin/catalog/support-points/",
            data=support_point_payload(test_domain, suffix=" throttle-b"),
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )

    assert first.status_code == 201
    assert int(response["Retry-After"]) >= 1
    assert_response_matches_openapi(response, expected_status=429)


@pytest.mark.django_db
def test_openapi_public_report_create_success_201(api_client, test_domain):
    data = {
        "region_slug": "alter-do-chao",
        "target_type": "route",
        "target_slug": "rota-pindobal",
        "report_type": "incorrect_info",
        "description": "Informação sobre ponto de parada está incorreta.",
        "reporter_contact": "contato@exemplo.com",
    }
    response = api_client.post("/api/v1/public/reports/", data=data, format="json")
    assert_response_matches_openapi(response, expected_status=201)


@pytest.mark.django_db
def test_openapi_public_report_create_invalid_400(api_client, test_domain):
    data = {
        "region_slug": "alter-do-chao",
        "target_type": "route",
        "target_slug": "rota-pindobal",
        "report_type": "incorrect_info",
        "description": "Curto",
    }
    response = api_client.post("/api/v1/public/reports/", data=data, format="json")
    assert_response_matches_openapi(response, expected_status=400)


@pytest.mark.django_db
def test_openapi_public_report_create_throttled_429(api_client, test_domain):
    cache.clear()
    data = {
        "region_slug": "alter-do-chao",
        "target_type": "route",
        "target_slug": "rota-pindobal",
        "report_type": "incorrect_info",
        "description": "Descrição válida com mais de 10 caracteres.",
    }
    responses = []
    for _ in range(12):
        responses.append(
            api_client.post(
                "/api/v1/public/reports/",
                data=data,
                format="json",
                HTTP_X_FORWARDED_FOR="192.168.1.100",
            )
        )
    throttled = [r for r in responses if r.status_code == 429]
    assert len(throttled) > 0
    for r in throttled:
        assert_response_matches_openapi(r, expected_status=429)


@pytest.mark.django_db
def test_openapi_events_batch_success_201(api_client, test_domain):
    data = {
        "consent_granted": True,
        "events": [
            {
                "event_id": str(uuid.uuid4()),
                "event_name": "route_opened",
                "occurred_at": timezone.now().isoformat(),
                "region_id": "alter-do-chao",
                "route_id": "rota-pindobal",
            }
        ],
    }
    response = api_client.post("/api/v1/events/batch", data=data, format="json")
    assert_response_matches_openapi(response, expected_status=201)


@pytest.mark.django_db
def test_openapi_events_batch_invalid_400(api_client):
    data = {
        "consent_granted": True,
        "events": [
            {
                "event_id": str(uuid.uuid4()),
                "event_name": "session_opened",
                "occurred_at": timezone.now().isoformat(),
                "region_id": "alter-do-chao",
                "email": "pii@exemplo.com",
            }
        ],
    }
    response = api_client.post("/api/v1/events/batch", data=data, format="json")
    assert_response_matches_openapi(response, expected_status=400)


@pytest.mark.django_db
def test_openapi_events_batch_throttled_429(api_client, test_domain):
    cache.clear()
    data = {
        "consent_granted": True,
        "events": [
            {
                "event_id": str(uuid.uuid4()),
                "event_name": "session_opened",
                "occurred_at": timezone.now().isoformat(),
                "region_id": "alter-do-chao",
            }
        ],
    }
    responses = []
    for _ in range(65):
        data["events"][0]["event_id"] = str(uuid.uuid4())
        responses.append(
            api_client.post(
                "/api/v1/events/batch",
                data=data,
                format="json",
                HTTP_X_FORWARDED_FOR="192.168.1.101",
            )
        )
    throttled = [r for r in responses if r.status_code == 429]
    assert len(throttled) > 0
    for r in throttled:
        assert_response_matches_openapi(r, expected_status=429)


@pytest.mark.django_db
def test_openapi_admin_reports_unauthenticated_403(api_client):
    response = api_client.get("/api/v1/admin/reports/")
    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_admin_reports_forbidden_403(api_client, unauthorized_user):
    api_client.force_authenticate(user=unauthorized_user)
    response = api_client.get("/api/v1/admin/reports/")
    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_admin_reports_success_200(api_client, admin_user, test_domain):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/admin/reports/")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_admin_report_patch_unauthenticated_403(api_client, test_domain):
    report_id = test_domain["report"].id
    response = api_client.patch(
        f"/api/v1/admin/reports/{report_id}/",
        data={"status": "reviewed"},
        format="json",
    )
    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_admin_report_patch_forbidden_403(api_client, unauthorized_user, test_domain):
    api_client.force_authenticate(user=unauthorized_user)
    report_id = test_domain["report"].id
    response = api_client.patch(
        f"/api/v1/admin/reports/{report_id}/",
        data={"status": "reviewed"},
        format="json",
    )
    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_admin_report_patch_not_found_404(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    random_uuid = str(uuid.uuid4())
    response = api_client.patch(
        f"/api/v1/admin/reports/{random_uuid}/",
        data={"status": "reviewed"},
        format="json",
    )
    assert_response_matches_openapi(response, expected_status=404)


@pytest.mark.django_db
def test_openapi_admin_report_patch_invalid_400(api_client, admin_user, test_domain):
    api_client.force_authenticate(user=admin_user)
    report_id = test_domain["report"].id
    response = api_client.patch(
        f"/api/v1/admin/reports/{report_id}/",
        data={"status": "invalido"},
        format="json",
    )
    assert_response_matches_openapi(response, expected_status=400)


@pytest.mark.django_db
def test_openapi_admin_report_patch_success_200(api_client, admin_user, test_domain):
    api_client.force_authenticate(user=admin_user)
    report_id = test_domain["report"].id
    response = api_client.patch(
        f"/api/v1/admin/reports/{report_id}/",
        data={"status": "reviewed", "moderation_note": "Moderação aprovada."},
        format="json",
    )
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_admin_analytics_summary_unauthenticated_403(api_client):
    response = api_client.get("/api/v1/admin/analytics/summary")
    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_admin_analytics_summary_forbidden_403(api_client, unauthorized_user):
    api_client.force_authenticate(user=unauthorized_user)
    response = api_client.get("/api/v1/admin/analytics/summary")
    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_admin_analytics_summary_success_200(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/admin/analytics/summary")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_admin_audit_logs_success_200(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/admin/audit-logs")
    assert_response_matches_openapi(response, expected_status=200)


@pytest.mark.django_db
def test_openapi_admin_dashboard_summary_unauthenticated_403(api_client):
    response = api_client.get("/api/v1/admin/dashboard/summary")
    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_admin_dashboard_summary_forbidden_403(api_client, unauthorized_user):
    api_client.force_authenticate(user=unauthorized_user)
    response = api_client.get("/api/v1/admin/dashboard/summary")
    assert_response_matches_openapi(response, expected_status=403)


@pytest.mark.django_db
def test_openapi_admin_dashboard_summary_success_200(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/admin/dashboard/summary")
    assert_response_matches_openapi(response, expected_status=200)
