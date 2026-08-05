import uuid

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from config.openapi_validator import assert_response_matches_openapi
from modules.accounts.models import AdministrativeRegionScope
from modules.accounts.permissions import ROLE_GROUP_PREFIX, AdminRole
from modules.core.models import EditorialStatus
from modules.publishing.models import EditorialRevision
from modules.regions.models import Region
from modules.reports.models import PublicReport

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_domain(db):
    region_tapajos = Region.objects.create(
        public_name="Tapajós",
        slug="tapajos",
        center_point="POINT(-54.7 -2.4)",
        status=EditorialStatus.PUBLISHED,
    )
    region_xingu = Region.objects.create(
        public_name="Xingu",
        slug="xingu",
        center_point="POINT(-52.0 -3.0)",
        status=EditorialStatus.PUBLISHED,
    )

    admin_group, _ = Group.objects.get_or_create(
        name=f"{ROLE_GROUP_PREFIX}{AdminRole.ADMINISTRATOR}"
    )
    admin_user = User.objects.create_user(
        username="admin_user", email="admin@exemplo.org", is_staff=True, is_active=True
    )
    admin_user.groups.add(admin_group)

    reviewer_group, _ = Group.objects.get_or_create(name=f"{ROLE_GROUP_PREFIX}{AdminRole.REVIEWER}")
    regional_reviewer = User.objects.create_user(
        username="reviewer_tapajos", email="rev@exemplo.org", is_staff=True, is_active=True
    )
    regional_reviewer.groups.add(reviewer_group)
    AdministrativeRegionScope.objects.create(
        user=regional_reviewer, region=region_tapajos, is_active=True
    )

    unauthorized_user = User.objects.create_user(
        username="no_perm_user", email="noperm@exemplo.org", is_staff=False, is_active=True
    )

    return {
        "region_tapajos": region_tapajos,
        "region_xingu": region_xingu,
        "admin_user": admin_user,
        "regional_reviewer": regional_reviewer,
        "unauthorized_user": unauthorized_user,
    }


@pytest.mark.django_db
def test_admin_dashboard_summary_unauthenticated(api_client):
    response = api_client.get("/api/v1/admin/dashboard/summary")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_admin_dashboard_summary_forbidden_user(api_client, setup_domain):
    api_client.force_authenticate(user=setup_domain["unauthorized_user"])
    response = api_client.get("/api/v1/admin/dashboard/summary")
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_dashboard_summary_regional_scope_authorization(api_client, setup_domain):
    reviewer = setup_domain["regional_reviewer"]
    api_client.force_authenticate(user=reviewer)

    # Acesso à região autorizada (Tapajós) -> 200 OK
    res_ok = api_client.get("/api/v1/admin/dashboard/summary?region_slug=tapajos")
    assert res_ok.status_code == 200
    assert res_ok.data["region_slug"] == "tapajos"

    # Acesso à região não autorizada (Xingu) -> 403 Forbidden
    res_forbidden = api_client.get("/api/v1/admin/dashboard/summary?region_slug=xingu")
    assert res_forbidden.status_code == 403


@pytest.mark.django_db
def test_admin_dashboard_summary_counts_by_state(api_client, setup_domain):
    admin = setup_domain["admin_user"]
    region_tapajos = setup_domain["region_tapajos"]
    api_client.force_authenticate(user=admin)

    # 1. Relato de segurança pendente (conta como alerta ativo E relato prioritário)
    PublicReport.objects.create(
        description="Alerta de tempestade na trilha.",
        region_slug="tapajos",
        report_type=PublicReport.ReportType.SAFETY_WARNING,
        status=PublicReport.Status.PENDING,
    )
    # 2. Relato de local fechado pendente (conta como relato prioritário, mas não alerta ativo)
    PublicReport.objects.create(
        description="Ponto de apoio fechado temporariamente.",
        region_slug="tapajos",
        report_type=PublicReport.ReportType.CLOSED_LOCATION,
        status=PublicReport.Status.PENDING,
    )
    # 3. Relato revisado (não entra nas contagens pendentes)
    PublicReport.objects.create(
        description="Informação incorreta já revisada.",
        region_slug="tapajos",
        report_type=PublicReport.ReportType.INCORRECT_INFO,
        status=PublicReport.Status.REVIEWED,
    )

    # 4. Revisão editorial em estado 'review' (aguardando aprovação)
    EditorialRevision.objects.create(
        region=region_tapajos,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id=uuid.uuid4(),
        sequence=1,
        status=EditorialRevision.Status.REVIEW,
        created_by=admin,
        updated_by=admin,
    )
    # 5. Revisão editorial em rascunho 'draft' (não pendente de aprovação)
    EditorialRevision.objects.create(
        region=region_tapajos,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id=uuid.uuid4(),
        sequence=1,
        status=EditorialRevision.Status.DRAFT,
        created_by=admin,
        updated_by=admin,
    )

    response = api_client.get("/api/v1/admin/dashboard/summary?region_slug=tapajos")
    assert response.status_code == 200
    assert response.data["region_slug"] == "tapajos"
    assert response.data["active_alerts_count"] == 1
    assert response.data["priority_reports_count"] == 2
    assert response.data["pending_revisions_count"] == 1


@pytest.mark.django_db
def test_admin_dashboard_summary_region_without_data(api_client, setup_domain):
    admin = setup_domain["admin_user"]
    api_client.force_authenticate(user=admin)

    response = api_client.get("/api/v1/admin/dashboard/summary?region_slug=xingu")
    assert response.status_code == 200
    assert response.data["region_slug"] == "xingu"
    assert response.data["active_alerts_count"] == 0
    assert response.data["priority_reports_count"] == 0
    assert response.data["pending_revisions_count"] == 0


@pytest.mark.django_db
def test_admin_dashboard_summary_openapi_compliance(api_client, setup_domain):
    admin = setup_domain["admin_user"]
    api_client.force_authenticate(user=admin)

    response = api_client.get("/api/v1/admin/dashboard/summary?region_slug=tapajos")
    assert_response_matches_openapi(response, expected_status=200)
