from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import RequestFactory
from drf_spectacular.generators import SchemaGenerator

from modules.accounts.permissions import AdminAction, AdminRole

from .models import AuditEvent
from .request_id import RequestIdMiddleware
from .service import record_audit_event
from .views import AuditEventListView


def test_audit_model_and_queryset_are_append_only():
    event = AuditEvent()
    event._state.adding = False

    with pytest.raises(ValidationError):
        event.save()
    with pytest.raises(ValidationError):
        event.delete()
    with pytest.raises(TypeError):
        AuditEvent.objects.all().update(result=AuditEvent.Result.SUCCESS)
    with pytest.raises(TypeError):
        AuditEvent.objects.all().delete()


def test_audit_service_rejects_metadata_outside_action_allowlist():
    with pytest.raises(ValidationError) as invalid:
        record_audit_event(
            actor=SimpleNamespace(pk=1),
            action=AuditEvent.Action.AUTH_LOGIN,
            target_type="administrative_user",
            target_id=1,
            request_id=uuid4(),
            metadata={"password": "não pode entrar"},
        )

    assert "allowlist" in str(invalid.value)


def test_audit_service_normalizes_safe_metadata():
    created = SimpleNamespace(pk=uuid4())
    request_id = uuid4()
    with patch(
        "modules.audit.service.AuditEvent.objects.create",
        return_value=created,
    ) as create:
        result = record_audit_event(
            actor=SimpleNamespace(pk=1),
            region=SimpleNamespace(pk=uuid4()),
            action=AuditEvent.Action.EDITORIAL_APPROVE,
            target_type="editorial_revision",
            target_id=uuid4(),
            request_id=request_id,
            metadata={
                "content_target_type": "route",
                "revision_sequence": 3,
                "change_count": 5,
            },
        )

    assert result is created
    assert create.call_args.kwargs["request_id"] == request_id
    assert create.call_args.kwargs["result"] == AuditEvent.Result.SUCCESS
    assert set(create.call_args.kwargs["metadata"]) == {
        "content_target_type",
        "revision_sequence",
        "change_count",
    }


def test_request_id_middleware_validates_header_and_echoes_uuid():
    request = RequestFactory().get("/", headers={"X-Request-ID": "inválido"})
    middleware = RequestIdMiddleware(lambda _request: HttpResponse())

    response = middleware(request)

    assert UUID(response["X-Request-ID"]) == request.request_id


def test_audit_endpoint_enforces_role_and_region_scope():
    queryset = MagicMock()
    queryset.filter.return_value = queryset
    queryset.__getitem__.return_value = []
    scopes = MagicMock()
    region_ids = ["region-a"]
    scopes.filter.return_value.values_list.return_value = region_ids
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
    queryset.filter.assert_called_once_with(region_id__in=region_ids)
    assert AuditEventListView.required_admin_action == AdminAction.VIEW_AUDIT

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/admin/audit-logs"]["get"]
    assert operation["operationId"] == "listAdminAuditEvents"
    assert operation["security"] == [{"cookieAuth": []}]
