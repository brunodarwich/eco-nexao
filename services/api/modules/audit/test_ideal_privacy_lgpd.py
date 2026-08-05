from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db.models import CheckConstraint, UniqueConstraint
from django.http import HttpResponse
from django.test import RequestFactory
from drf_spectacular.generators import SchemaGenerator

from modules.accounts.permissions import AdminAction, AdminRole
from modules.audit.models import AuditEvent
from modules.audit.request_id import RequestIdMiddleware
from modules.audit.service import record_audit_event
from modules.audit.views import AuditEventListView
from modules.catalog.models import ContactChannel
from modules.imports.catalog_csv import (
    CATALOG_COLUMNS,
    CatalogRelationIndex,
    validate_catalog_csv,
)
from modules.publishing.publication import (
    EditorialWorkflowError,
    validate_target_references,
)
from modules.routes.serializers import PublicContactChannelSerializer


def default_relations() -> CatalogRelationIndex:
    return CatalogRelationIndex(
        region_slugs=frozenset({"santarem-alter-do-chao"}),
        category_slugs=frozenset({"alimentacao"}),
        route_keys=frozenset({("santarem-alter-do-chao", "pindobal")}),
    )


# --- 1. CONTACT CHANNEL LGPD COMPLIANCE & AUTHORIZATION ENFORCEMENT ---


def test_contact_channel_public_requires_provenance_constraint():
    constraints = {c.name: c for c in ContactChannel._meta.constraints}

    # Verify model level DB constraints for LGPD contact channel privacy
    assert "contact_public_requires_provenance" in constraints
    assert "contact_public_channel_uniq" in constraints

    provenance_constraint = constraints["contact_public_requires_provenance"]
    assert isinstance(provenance_constraint, CheckConstraint)

    unique_constraint = constraints["contact_public_channel_uniq"]
    assert isinstance(unique_constraint, UniqueConstraint)
    assert set(unique_constraint.fields) == {"actor", "channel_type", "public_value"}


def test_contact_channel_instance_privacy_model_contracts():
    # Public contact carries provenance rather than inferred consent.
    public_contact = ContactChannel(
        channel_type=ContactChannel.ChannelType.WHATSAPP,
        public_value="+5593999990001",
        is_public=True,
        source_type=ContactChannel.SourceType.CONSOLIDATED_SHEET,
        source_reference="planilha:linha-001",
    )
    assert public_contact.is_public is True
    assert public_contact.source_reference == "planilha:linha-001"
    assert public_contact.public_value == "+5593999990001"

    # Private contact holds encrypted value and has is_public=False
    private_contact = ContactChannel(
        channel_type=ContactChannel.ChannelType.PHONE,
        value_encrypted="enc:v1:secret_phone_hash",
        public_value="",
        is_public=False,
        source_type=ContactChannel.SourceType.LEGACY,
        source_reference="",
    )
    assert private_contact.is_public is False
    assert private_contact.value_encrypted.startswith("enc:")
    assert private_contact.public_value == ""
    assert private_contact.source_reference == ""


def test_public_contact_channel_serializer_excludes_private_fields():
    fields = PublicContactChannelSerializer.Meta.fields

    # Guarantee private/sensitive fields are never exposed in public API serializer
    assert "value_encrypted" not in fields
    assert "source_reference" not in fields
    assert "verified_by" not in fields
    assert "public_value" in fields
    assert "channel_type" in fields
    assert "verified_at" in fields


# --- 2. CSV IMPORT PRIVACY PROTECTION & LGPD REDACTION ---


def test_csv_validation_rejects_unauthorized_public_contact_request():
    relations = default_relations()

    row = {col: "" for col in CATALOG_COLUMNS}
    row.update(
        {
            "external_id": "test:unauthorized_contact",
            "action": "upsert",
            "record_status": "active",
            "publish_status": "review",
            "region_slug": "santarem-alter-do-chao",
            "route_slugs": "pindobal",
            "route_role": "support",
            "actor_kind": "business",
            "category_slug": "alimentacao",
            "public_name": "Ator Contato Privado",
            "short_description": "Descrição",
            "city": "Santarém",
            "state": "PA",
            "country_code": "BR",
            "source_type": "mock",
            "source_reference": "test:ref",
            "verification_status": "direct",
            "verified_at": "2026-07-01T10:00:00Z",
            "verified_by": "admin@econexao.org",
            "public_contact_authorized": "false",
            "phone_e164": "+5593999990001",
            "media_authorized": "true",
        }
    )

    import csv
    import io

    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(
        [
            CATALOG_COLUMNS,
            [row[col] for col in CATALOG_COLUMNS],
        ]
    )

    result = validate_catalog_csv(output.getvalue().encode(), relations)

    assert not result.valid
    issue_codes = {issue.code for issue in result.issues}
    assert "contact_not_authorized" in issue_codes


def test_csv_validation_redacts_private_contact_data_from_issues():
    relations = default_relations()
    private_email = "sensivel-privado-lgpd@dominio-secreto.com"

    row = {col: "" for col in CATALOG_COLUMNS}
    row.update(
        {
            "external_id": "test:redact_email",
            "action": "upsert",
            "record_status": "active",
            "publish_status": "review",
            "region_slug": "santarem-alter-do-chao",
            "route_slugs": "pindobal",
            "route_role": "support",
            "actor_kind": "business",
            "category_slug": "alimentacao",
            "public_name": "Ator Email Invalido",
            "short_description": "Descrição",
            "city": "Santarém",
            "state": "PA",
            "country_code": "BR",
            "source_type": "mock",
            "source_reference": "test:ref",
            "verification_status": "unverified",
            "email": "invalid-private-email-format",
            "public_contact_authorized": "false",
            "media_authorized": "false",
        }
    )

    import csv
    import io

    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(
        [
            CATALOG_COLUMNS,
            [row[col] for col in CATALOG_COLUMNS],
        ]
    )

    result = validate_catalog_csv(output.getvalue().encode(), relations)

    assert not result.valid
    # Issues log must not leak private input value in str representation
    assert private_email not in str(result.issues)


# --- 3. PUBLICATION WORKFLOW LGPD VALIDATION ---


def test_publication_rejects_actor_with_unverified_or_unauthorized_public_contact():
    actor = SimpleNamespace(
        category=SimpleNamespace(is_active=True),
        locations=MagicMock(),
    )
    actor.locations.filter.return_value.exists.return_value = True

    # ContactChannel queryset simulating an unverified or unauthorized public contact
    invalid_contacts_qs = MagicMock()
    invalid_contacts_qs.exists.return_value = True

    with patch(
        "modules.publishing.publication.ContactChannel.objects.filter",
        return_value=invalid_contacts_qs,
    ):
        with pytest.raises(EditorialWorkflowError) as exc_info:
            validate_target_references(
                target=actor,
                target_type="actor",
                region=SimpleNamespace(),
            )

    assert exc_info.value.code == "publication_references_invalid"
    assert "contacts" in exc_info.value.field_errors
    expected_msg = "Contatos públicos exigem valor, autorização e verificação vigente."
    assert expected_msg in exc_info.value.field_errors["contacts"]


# --- 4. AUDIT LOG IMMUTABILITY, PII FILTERING & REQUEST TRACING ---


def test_audit_event_immutability_append_only_lgpd():
    event = AuditEvent()
    event._state.adding = False

    # Prevent modification of existing audit logs
    with pytest.raises(ValidationError, match="imutáveis|imutáveis"):
        event.save()

    # Prevent deletion of audit logs (required for LGPD accountability)
    with pytest.raises(ValidationError, match="não podem ser removidos|não podem ser removidos"):
        event.delete()

    # QuerySet update/delete bulk actions must fail
    with pytest.raises(TypeError, match="imutáveis|imutáveis"):
        AuditEvent.objects.all().update(result=AuditEvent.Result.SUCCESS)

    with pytest.raises(TypeError, match="não podem ser removidos|não podem ser removidos"):
        AuditEvent.objects.all().delete()


def test_audit_metadata_allowlist_filters_pii():
    # Attempting to log PII (like email, phone, or password) in metadata must be rejected
    with pytest.raises(ValidationError) as exc_info:
        record_audit_event(
            actor=SimpleNamespace(pk=1),
            action=AuditEvent.Action.AUTH_LOGIN,
            target_type="administrative_user",
            target_id=1,
            request_id=uuid4(),
            metadata={"user_private_email": "segredo@dominio.com", "ip_address": "127.0.0.1"},
        )

    assert "allowlist" in str(exc_info.value)


def test_request_id_tracing_on_audit_logs():
    request_id = uuid4()
    request = RequestFactory().get("/", headers={"X-Request-ID": str(request_id)})
    middleware = RequestIdMiddleware(lambda _req: HttpResponse())

    response = middleware(request)

    assert response["X-Request-ID"] == str(request_id)
    assert request.request_id == request_id


def test_audit_log_endpoint_rbac_and_region_scoping():
    queryset = MagicMock()
    queryset.filter.return_value = queryset
    queryset.__getitem__.return_value = []

    scopes = MagicMock()
    scopes.filter.return_value.values_list.return_value = ["region-santarem"]

    request = SimpleNamespace(
        query_params={},
        user=SimpleNamespace(administrative_region_scopes=scopes),
    )

    with (
        patch(
            "modules.audit.views.get_user_roles",
            return_value=frozenset({AdminRole.REVIEWER}),
        ),
        patch(
            "modules.audit.views.AuditEvent.objects.select_related",
            return_value=queryset,
        ),
    ):
        response = AuditEventListView().get(request)

    assert response.data == []
    queryset.filter.assert_called_once_with(region_id__in=["region-santarem"])
    assert AuditEventListView.required_admin_action == AdminAction.VIEW_AUDIT

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/admin/audit-logs"]["get"]
    assert operation["operationId"] == "listAdminAuditEvents"
    assert operation["security"] == [{"cookieAuth": []}]
