from collections.abc import Mapping
from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError

from .models import AuditEvent
from .request_id import normalize_request_id

AUDIT_METADATA_FIELDS: dict[str, dict[str, type]] = {
    AuditEvent.Action.AUTH_LOGIN: {},
    AuditEvent.Action.AUTH_LOGOUT: {},
    AuditEvent.Action.EDITORIAL_APPROVE: {
        "content_target_type": str,
        "revision_sequence": int,
        "change_count": int,
    },
    AuditEvent.Action.PUBLICATION_PUBLISH: {
        "content_target_type": str,
        "content_target_id": str,
        "publication_id": str,
        "version": int,
        "checksum": str,
        "critical_override": bool,
    },
    AuditEvent.Action.PUBLICATION_RESTORE: {
        "content_target_type": str,
        "content_target_id": str,
        "publication_id": str,
        "source_publication_id": str,
        "version": int,
        "source_version": int,
        "checksum": str,
        "critical_override": bool,
    },
    AuditEvent.Action.EXTERNAL_DISCOVERY: {
        "provider": str,
        "route_id": str,
        "result_count": int,
        "radius_meters": int,
        "max_results": int,
        "type_count": int,
    },
    AuditEvent.Action.IMPORT_COMMIT: {
        "sha256": str,
        "row_count": int,
        "warning_count": int,
        "create_count": int,
        "update_count": int,
        "archive_count": int,
    },
}


def _validate_metadata(action: str, metadata: Mapping[str, Any]) -> dict[str, Any]:
    schema = AUDIT_METADATA_FIELDS.get(action)
    if schema is None:
        raise ValidationError({"action": ["Ação de auditoria inválida."]})
    supplied = set(metadata)
    expected = set(schema)
    if supplied != expected:
        raise ValidationError({"metadata": ["Os metadados não correspondem à allowlist da ação."]})
    normalized: dict[str, Any] = {}
    for key, expected_type in schema.items():
        value = metadata[key]
        if expected_type is int and isinstance(value, bool):
            valid_type = False
        else:
            valid_type = isinstance(value, expected_type)
        if not valid_type:
            raise ValidationError({"metadata": [f"O campo {key} possui tipo inválido."]})
        if isinstance(value, str) and (not value or len(value) > 128):
            raise ValidationError({"metadata": [f"O campo {key} possui tamanho inválido."]})
        normalized[key] = value
    return normalized


def record_audit_event(
    *,
    actor: Any,
    action: str,
    target_type: str,
    target_id: Any,
    request_id: UUID | str | None,
    region: Any | None = None,
    reason: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> AuditEvent:
    normalized_target_type = target_type.strip()
    normalized_target_id = str(target_id).strip()
    normalized_reason = reason.strip()
    if not normalized_target_type or len(normalized_target_type) > 64:
        raise ValidationError({"target_type": ["Alvo de auditoria inválido."]})
    if not normalized_target_id or len(normalized_target_id) > 128:
        raise ValidationError({"target_id": ["Identificador de alvo inválido."]})
    if len(normalized_reason) > 2000:
        raise ValidationError({"reason": ["O motivo excede 2.000 caracteres."]})
    normalized_metadata = _validate_metadata(action, metadata or {})
    return AuditEvent.objects.create(
        actor=actor,
        region=region,
        action=action,
        target_type=normalized_target_type,
        target_id=normalized_target_id,
        request_id=normalize_request_id(request_id),
        reason=normalized_reason,
        metadata=normalized_metadata,
        result=AuditEvent.Result.SUCCESS,
    )


def record_authentication_event(
    *,
    actor: Any,
    action: str,
    request_id: UUID | str | None,
) -> AuditEvent:
    if action not in {
        AuditEvent.Action.AUTH_LOGIN,
        AuditEvent.Action.AUTH_LOGOUT,
    }:
        raise ValidationError({"action": ["Ação de autenticação inválida."]})
    return record_audit_event(
        actor=actor,
        action=action,
        target_type="administrative_user",
        target_id=actor.pk,
        request_id=request_id,
    )
