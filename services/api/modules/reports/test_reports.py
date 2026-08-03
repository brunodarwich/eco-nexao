from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from modules.accounts.models import AdministrativeRegionScope
from modules.audit.models import AuditEvent
from modules.regions.models import Region
from modules.reports.models import PublicReport
from modules.reports.serializers import (
    AdminReportSerializer,
    PublicReportCreateSerializer,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_public_report_create_serializer_valid():
    from modules.catalog.models import Actor, ActorLocation, Category
    from modules.core.models import EditorialStatus
    from modules.regions.models import Region

    region = Region.objects.create(
        public_name="Tapajós",
        slug="tapajos",
        center_point="POINT(-54.7 -2.4)",
        status=EditorialStatus.PUBLISHED,
    )
    cat = Category.objects.create(slug="alimentacao", public_name="Alimentação")
    actor = Actor.objects.create(
        external_id="act-1",
        actor_kind="business",
        category=cat,
        slug="cozinha-do-tapajos",
        public_name="Cozinha do Tapajós",
        short_description="Desc",
        editorial_status=EditorialStatus.PUBLISHED,
    )
    ActorLocation.objects.create(
        actor=actor,
        region=region,
        label="Sede",
        is_primary=True,
        public_visibility=True,
    )

    data = {
        "description": "O horário de atendimento mudou para 11h às 22h.",
        "region_slug": "tapajos",
        "report_type": "incorrect_info",
        "reporter_contact": "visitante@exemplo.org",
        "target_slug": "cozinha-do-tapajos",
        "target_type": "actor",
    }
    serializer = PublicReportCreateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert (
        serializer.validated_data["description"]
        == "O horário de atendimento mudou para 11h às 22h."
    )


def test_public_report_create_serializer_invalid_short_description():
    data = {
        "description": "Curto",
        "report_type": "incorrect_info",
    }
    serializer = PublicReportCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert "description" in serializer.errors


def test_admin_report_serializer_valid():
    report = PublicReport(
        description="O horário de atendimento mudou para 11h às 22h.",
        id="123e4567-e89b-12d3-a456-426614174000",
        report_type="incorrect_info",
        status="pending",
    )
    serializer = AdminReportSerializer(report)
    assert serializer.data["status"] == "pending"
    assert serializer.data["description"] == "O horário de atendimento mudou para 11h às 22h."


@pytest.mark.django_db
@patch("modules.reports.views.PublicReport.objects.create")
def test_public_create_report_endpoint(mock_create, api_client):
    from django.core.cache import cache

    from modules.catalog.models import Actor, ActorLocation, Category
    from modules.core.models import EditorialStatus
    from modules.regions.models import Region

    cache.clear()

    region = Region.objects.create(
        public_name="Tapajós",
        slug="tapajos",
        center_point="POINT(-54.7 -2.4)",
        status=EditorialStatus.PUBLISHED,
    )
    cat = Category.objects.create(slug="alimentacao", public_name="Alimentação")
    actor = Actor.objects.create(
        external_id="act-1",
        actor_kind="business",
        category=cat,
        slug="cozinha-do-tapajos",
        public_name="Cozinha do Tapajós",
        short_description="Desc",
        editorial_status=EditorialStatus.PUBLISHED,
    )
    ActorLocation.objects.create(
        actor=actor,
        region=region,
        label="Sede",
        is_primary=True,
        public_visibility=True,
    )

    mock_report = PublicReport(
        description="O horário de atendimento mudou para 11h às 22h.",
        id="123e4567-e89b-12d3-a456-426614174000",
        status="pending",
    )
    mock_create.return_value = mock_report

    response = api_client.post(
        "/api/v1/public/reports/",
        {
            "description": "O horário de atendimento mudou para 11h às 22h.",
            "region_slug": "tapajos",
            "report_type": "incorrect_info",
            "reporter_contact": "visitante@exemplo.org",
            "target_slug": "cozinha-do-tapajos",
            "target_type": "actor",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert response.data["status"] == "pending"


def test_admin_report_list_unauthenticated(api_client):
    response = api_client.get("/api/v1/admin/reports/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_admin_moderate_report_success_with_audit(api_client):
    admin_group, _ = Group.objects.get_or_create(name="econexao:administrator")
    user = User.objects.create_user(username="admin_editor", is_staff=True, is_active=True)
    user.groups.add(admin_group)
    api_client.force_authenticate(user=user)

    report = PublicReport.objects.create(
        description="O horário de atendimento mudou para 11h às 22h.",
        region_slug="tapajos",
        report_type="incorrect_info",
        reporter_contact="visitante@exemplo.org",
        status="pending",
        target_slug="cozinha-do-tapajos",
        target_type="actor",
    )

    response = api_client.patch(
        f"/api/v1/admin/reports/{report.id}/",
        {
            "moderation_note": "Verificado com o estabelecimento.",
            "status": "reviewed",
        },
        format="json",
    )
    assert response.status_code == 200
    assert response.data["status"] == "reviewed"
    assert response.data["moderation_note"] == "Verificado com o estabelecimento."

    report.refresh_from_db()
    assert report.status == "reviewed"
    assert report.moderation_note == "Verificado com o estabelecimento."

    audit_event = AuditEvent.objects.get(target_id=str(report.id))
    assert audit_event.action == AuditEvent.Action.REPORT_MODERATE
    assert audit_event.metadata["previous_status"] == "pending"
    assert audit_event.metadata["new_status"] == "reviewed"


@pytest.mark.django_db
def test_admin_moderate_report_atomic_rollback_on_audit_failure(api_client):
    """
    Testa que uma falha ao registrar auditoria reverte inteiramente a moderação
    do relato (transaction.atomic), sem persistir estado parcial.
    """
    admin_group, _ = Group.objects.get_or_create(name="econexao:administrator")
    user = User.objects.create_user(username="admin_editor", is_staff=True, is_active=True)
    user.groups.add(admin_group)
    api_client.force_authenticate(user=user)

    report = PublicReport.objects.create(
        description="O horário de atendimento mudou para 11h às 22h.",
        region_slug="tapajos",
        report_type="incorrect_info",
        reporter_contact="visitante@exemplo.org",
        status="pending",
        target_slug="cozinha-do-tapajos",
        target_type="actor",
    )

    audit_err = RuntimeError("Audit DB Error")
    with patch("modules.reports.views.record_audit_event", side_effect=audit_err):
        try:
            api_client.patch(
                f"/api/v1/admin/reports/{report.id}/",
                {
                    "moderation_note": "Nota de teste.",
                    "status": "reviewed",
                },
                format="json",
            )
        except RuntimeError:
            pass

    report.refresh_from_db()
    assert report.status == "pending", f"Esperado 'pending', mas foi '{report.status}'"
    assert report.moderation_note == "", f"Esperado '', mas foi '{report.moderation_note}'"


@pytest.mark.django_db
def test_admin_reports_role_and_regional_authorization(api_client):
    region_tapajos = Region.objects.create(
        public_name="Tapajós", slug="tapajos", center_point="POINT(-54.7 -2.4)"
    )
    Region.objects.create(public_name="Xingu", slug="xingu", center_point="POINT(-52.0 -3.0)")

    report_tapajos = PublicReport.objects.create(
        description="Informação incorreta no Tapajós.",
        region_slug="tapajos",
        report_type="incorrect_info",
        reporter_contact="tapajos@exemplo.org",
        status="pending",
        target_slug="ponto-tapajos",
        target_type="actor",
    )
    report_xingu = PublicReport.objects.create(
        description="Informação incorreta no Xingu.",
        region_slug="xingu",
        report_type="incorrect_info",
        reporter_contact="xingu@exemplo.org",
        status="pending",
        target_slug="ponto-xingu",
        target_type="actor",
    )

    # 1. Usuário comum (não staff) -> 403
    common_user = User.objects.create_user(username="common", is_staff=False)
    api_client.force_authenticate(user=common_user)
    assert api_client.get("/api/v1/admin/reports/").status_code == 403

    # 2. Staff sem grupo/papel -> 403
    staff_no_role = User.objects.create_user(username="staff_norole", is_staff=True)
    api_client.force_authenticate(user=staff_no_role)
    assert api_client.get("/api/v1/admin/reports/").status_code == 403

    # 3. Editor com escopo para Tapajós (pode listar Tapajós, não moderar, não vê contato)
    editor_group, _ = Group.objects.get_or_create(name="econexao:editor")
    editor = User.objects.create_user(username="editor_user", is_staff=True)
    editor.groups.add(editor_group)
    AdministrativeRegionScope.objects.create(user=editor, region=region_tapajos, is_active=True)

    api_client.force_authenticate(user=editor)
    res = api_client.get("/api/v1/admin/reports/")
    assert res.status_code == 200
    returned_ids = [item["id"] for item in res.data]
    assert str(report_tapajos.id) in returned_ids
    assert str(report_xingu.id) not in returned_ids
    # Contato do relator é omitido/limpo para editor
    assert res.data[0]["reporter_contact"] == ""

    # Editor tentando moderar -> 403
    mod_res = api_client.patch(
        f"/api/v1/admin/reports/{report_tapajos.id}/",
        {"status": "reviewed"},
        format="json",
    )
    assert mod_res.status_code == 403

    # 4. Reviewer com escopo para Tapajós (pode moderar Tapajós e vê contato, 403 no Xingu)
    reviewer_group, _ = Group.objects.get_or_create(name="econexao:reviewer")
    reviewer = User.objects.create_user(username="reviewer_user", is_staff=True)
    reviewer.groups.add(reviewer_group)
    AdministrativeRegionScope.objects.create(user=reviewer, region=region_tapajos, is_active=True)

    api_client.force_authenticate(user=reviewer)
    res_rev = api_client.get("/api/v1/admin/reports/")
    assert res_rev.data[0]["reporter_contact"] == "tapajos@exemplo.org"

    mod_ok = api_client.patch(
        f"/api/v1/admin/reports/{report_tapajos.id}/",
        {"status": "reviewed"},
        format="json",
    )
    assert mod_ok.status_code == 200

    mod_xingu = api_client.patch(
        f"/api/v1/admin/reports/{report_xingu.id}/",
        {"status": "reviewed"},
        format="json",
    )
    assert mod_xingu.status_code == 403


@pytest.mark.django_db
def test_public_create_report_throttling_and_no_persistence(api_client):
    from django.core.cache import cache

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

    payload = {
        "description": "Relato para testar throttling no endpoint.",
        "region_slug": "tapajos",
        "report_type": "incorrect_info",
        "reporter_contact": "throttle@exemplo.org",
        "target_slug": "pindobal",
        "target_type": "route",
    }

    initial_count = PublicReport.objects.count()

    # O limite padrão é 5/hour
    for i in range(5):
        res = api_client.post("/api/v1/public/reports/", payload, format="json")
        assert res.status_code == 201, f"Falhou na tentativa {i + 1}"

    # A 6ª tentativa deve ser bloqueada com HTTP 429
    blocked_res = api_client.post("/api/v1/public/reports/", payload, format="json")
    assert blocked_res.status_code == 429
    assert "detail" in blocked_res.data

    # Confirmar que requisições bloqueadas não persistem relatos adicionais
    final_count = PublicReport.objects.count()
    assert final_count == initial_count + 5


@pytest.mark.django_db
def test_public_create_report_target_validation(api_client):
    from django.core.cache import cache

    from modules.catalog.models import Actor, ActorLocation, Category
    from modules.core.models import EditorialStatus
    from modules.regions.models import Region
    from modules.routes.models import Route

    cache.clear()

    region_tapajos = Region.objects.create(
        public_name="Tapajós",
        slug="tapajos",
        center_point="POINT(-54.7 -2.4)",
        status=EditorialStatus.PUBLISHED,
    )

    # 1. Região inexistente -> 400
    res_inv_region = api_client.post(
        "/api/v1/public/reports/",
        {
            "description": "Descrição com mais de dez caracteres.",
            "region_slug": "regiao-inexistente",
            "report_type": "incorrect_info",
            "target_type": "general",
        },
        format="json",
    )
    assert res_inv_region.status_code == 400
    assert "region_slug" in res_inv_region.data

    # 2. Rota rascunho (não publicada) -> 400
    Route.objects.create(
        region=region_tapajos,
        slug="rota-draft",
        public_name="Rota Rascunho",
        short_promise="Promessa",
        duration_minutes=60,
        difficulty="easy",
        editorial_status=EditorialStatus.DRAFT,
    )
    res_draft_route = api_client.post(
        "/api/v1/public/reports/",
        {
            "description": "Relato sobre rota rascunho.",
            "region_slug": "tapajos",
            "report_type": "incorrect_info",
            "target_slug": "rota-draft",
            "target_type": "route",
        },
        format="json",
    )
    assert res_draft_route.status_code == 400
    assert "target_slug" in res_draft_route.data

    # 3. Rota publicada -> 201
    Route.objects.create(
        region=region_tapajos,
        slug="rota-publicada",
        public_name="Rota Publicada",
        short_promise="Promessa",
        duration_minutes=60,
        difficulty="easy",
        editorial_status=EditorialStatus.PUBLISHED,
    )
    res_pub_route = api_client.post(
        "/api/v1/public/reports/",
        {
            "description": "Relato sobre rota publicada válida.",
            "region_slug": "tapajos",
            "report_type": "incorrect_info",
            "target_slug": "rota-publicada",
            "target_type": "route",
        },
        format="json",
    )
    assert res_pub_route.status_code == 201

    # 4. Ator sem localização ou em outra região -> 400
    cat = Category.objects.create(slug="alimentacao", public_name="Alimentação")
    actor = Actor.objects.create(
        external_id="act-1",
        actor_kind="business",
        category=cat,
        slug="ator-teste",
        public_name="Ator Teste",
        short_description="Desc",
        editorial_status=EditorialStatus.PUBLISHED,
    )
    res_actor_noloc = api_client.post(
        "/api/v1/public/reports/",
        {
            "description": "Relato sobre ator sem localização.",
            "region_slug": "tapajos",
            "report_type": "incorrect_info",
            "target_slug": "ator-teste",
            "target_type": "actor",
        },
        format="json",
    )
    assert res_actor_noloc.status_code == 400

    # Adicionar localização na região
    ActorLocation.objects.create(
        actor=actor,
        region=region_tapajos,
        label="Sede",
        is_primary=True,
        public_visibility=True,
    )
    res_actor_ok = api_client.post(
        "/api/v1/public/reports/",
        {
            "description": "Relato sobre ator válido publicado.",
            "region_slug": "tapajos",
            "report_type": "incorrect_info",
            "target_slug": "ator-teste",
            "target_type": "actor",
        },
        format="json",
    )
    assert res_actor_ok.status_code == 201


@pytest.mark.django_db
def test_admin_moderate_report_immutable_original_content(api_client):
    admin_group, _ = Group.objects.get_or_create(name="econexao:administrator")
    user = User.objects.create_user(username="admin_editor2", is_staff=True, is_active=True)
    user.groups.add(admin_group)
    api_client.force_authenticate(user=user)

    report = PublicReport.objects.create(
        description="Descrição original e verdadeira.",
        region_slug="tapajos",
        report_type="incorrect_info",
        reporter_contact="original@exemplo.org",
        status="pending",
        target_slug="ponto-tapajos",
        target_type="general",
    )

    # Tentativa de alteração abusiva de conteúdo e contato via PATCH na moderação
    res = api_client.patch(
        f"/api/v1/admin/reports/{report.id}/",
        {
            "description": "Descrição adulterada por invasor/moderador.",
            "reporter_contact": "hacker@exemplo.org",
            "target_slug": "alvo-adulterado",
            "status": "reviewed",
            "moderation_note": "Nota válida.",
        },
        format="json",
    )
    assert res.status_code == 200

    report.refresh_from_db()
    # Status e nota devem atualizar
    assert report.status == "reviewed"
    assert report.moderation_note == "Nota válida."

    # Campos originais fornecidos pelo relator devem se manter estritamente imutáveis
    assert report.description == "Descrição original e verdadeira."
    assert report.reporter_contact == "original@exemplo.org"
    assert report.target_slug == "ponto-tapajos"
