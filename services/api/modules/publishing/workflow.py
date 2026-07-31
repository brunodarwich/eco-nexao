import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from django.db import transaction
from django.utils import timezone

from modules.audit.models import AuditEvent
from modules.audit.service import record_audit_event
from modules.catalog.models import Actor, ActorLocation, RouteActor
from modules.regions.models import Region
from modules.routes.models import Route

from .models import EditorialRevision

MAX_SNAPSHOT_BYTES = 256 * 1024
_MISSING = object()


@dataclass(frozen=True, slots=True)
class EditorialWorkflowError(Exception):
    code: str
    message: str
    status_code: int = 400
    field_errors: dict[str, list[str]] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


def validate_snapshot(snapshot: Any) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise EditorialWorkflowError(
            code="invalid_snapshot",
            message="O snapshot editorial deve ser um objeto JSON.",
            field_errors={"snapshot": ["Informe um objeto JSON."]},
        )
    try:
        encoded = json.dumps(
            snapshot,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise EditorialWorkflowError(
            code="invalid_snapshot",
            message="O snapshot editorial contém valores inválidos.",
            field_errors={"snapshot": ["Use somente valores JSON válidos."]},
        ) from error
    if len(encoded) > MAX_SNAPSHOT_BYTES:
        raise EditorialWorkflowError(
            code="snapshot_too_large",
            message="O snapshot editorial excede o limite permitido.",
            status_code=413,
            field_errors={"snapshot": ["O limite é de 256 KiB."]},
        )
    return deepcopy(snapshot)


def _json_pointer(path: str, key: str) -> str:
    escaped = key.replace("~", "~0").replace("/", "~1")
    return f"{path}/{escaped}" if path else f"/{escaped}"


def build_snapshot_diff(
    before: Any,
    after: Any,
    *,
    path: str = "",
) -> list[dict[str, Any]]:
    if isinstance(before, dict) and isinstance(after, dict):
        changes: list[dict[str, Any]] = []
        for key in sorted(before.keys() | after.keys()):
            child_path = _json_pointer(path, str(key))
            old_value = before.get(key, _MISSING)
            new_value = after.get(key, _MISSING)
            if old_value is _MISSING:
                changes.append(
                    {"operation": "add", "path": child_path, "before": None, "after": new_value}
                )
            elif new_value is _MISSING:
                changes.append(
                    {"operation": "remove", "path": child_path, "before": old_value, "after": None}
                )
            else:
                changes.extend(build_snapshot_diff(old_value, new_value, path=child_path))
        return changes
    if before == after:
        return []
    return [
        {
            "operation": "replace",
            "path": path or "/",
            "before": before,
            "after": after,
        }
    ]


def _require_lock_version(revision: EditorialRevision, expected_lock_version: int) -> None:
    if revision.lock_version != expected_lock_version:
        raise EditorialWorkflowError(
            code="revision_conflict",
            message="O rascunho foi alterado por outra operação.",
            status_code=409,
            field_errors={"lock_version": ["Recarregue a revisão e compare as mudanças."]},
        )


def _require_status(revision: EditorialRevision, expected_status: str) -> None:
    if revision.status != expected_status:
        raise EditorialWorkflowError(
            code="invalid_revision_state",
            message="A revisão não está no estado exigido para esta ação.",
            status_code=409,
        )


def apply_snapshot_update(
    revision: EditorialRevision,
    *,
    snapshot: Any,
    expected_lock_version: int,
    user: Any,
) -> None:
    _require_status(revision, EditorialRevision.Status.DRAFT)
    _require_lock_version(revision, expected_lock_version)
    revision.snapshot = validate_snapshot(snapshot)
    revision.diff = build_snapshot_diff(revision.base_snapshot, revision.snapshot)
    revision.updated_by = user
    revision.lock_version += 1


def apply_submission(
    revision: EditorialRevision,
    *,
    expected_lock_version: int,
    user: Any,
) -> None:
    _require_status(revision, EditorialRevision.Status.DRAFT)
    _require_lock_version(revision, expected_lock_version)
    revision.status = EditorialRevision.Status.REVIEW
    revision.submitted_by = user
    revision.submitted_at = timezone.now()
    revision.updated_by = user
    revision.lock_version += 1


def apply_return(
    revision: EditorialRevision,
    *,
    expected_lock_version: int,
    reason: str,
    user: Any,
) -> None:
    _require_status(revision, EditorialRevision.Status.REVIEW)
    _require_lock_version(revision, expected_lock_version)
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise EditorialWorkflowError(
            code="return_reason_required",
            message="A devolução exige um motivo.",
            field_errors={"reason": ["Informe o que precisa ser corrigido."]},
        )
    revision.status = EditorialRevision.Status.DRAFT
    revision.reviewed_by = user
    revision.reviewed_at = timezone.now()
    revision.return_reason = normalized_reason
    revision.updated_by = user
    revision.lock_version += 1


def apply_approval(
    revision: EditorialRevision,
    *,
    expected_lock_version: int,
    user: Any,
) -> None:
    _require_status(revision, EditorialRevision.Status.REVIEW)
    _require_lock_version(revision, expected_lock_version)
    if revision.submitted_by_id == user.pk:
        raise EditorialWorkflowError(
            code="review_segregation_required",
            message="A pessoa que enviou a revisão não pode aprová-la.",
            status_code=403,
        )
    revision.status = EditorialRevision.Status.APPROVED
    revision.reviewed_by = user
    revision.reviewed_at = timezone.now()
    revision.return_reason = ""
    revision.updated_by = user
    revision.lock_version += 1


def resolve_target_region(
    *,
    target_type: str,
    target_id: Any,
    actor_region_id: Any | None = None,
    for_update: bool = False,
) -> Region:
    if target_type == EditorialRevision.TargetType.REGION:
        queryset = Region.objects.select_for_update() if for_update else Region.objects
        return queryset.get(pk=target_id)
    if target_type == EditorialRevision.TargetType.ROUTE:
        queryset = Route.objects.select_for_update() if for_update else Route.objects
        return queryset.select_related("region").get(pk=target_id).region
    if target_type == EditorialRevision.TargetType.ACTOR:
        if actor_region_id is None:
            raise EditorialWorkflowError(
                code="actor_region_required",
                message="A revisão de ator exige uma região editorial.",
                field_errors={"region_id": ["Informe uma região vinculada ao ator."]},
            )
        queryset = Actor.objects.select_for_update() if for_update else Actor.objects
        actor = queryset.get(pk=target_id)
        belongs_to_region = (
            ActorLocation.objects.filter(
                actor=actor,
                region_id=actor_region_id,
            ).exists()
            or RouteActor.objects.filter(
                actor=actor,
                route__region_id=actor_region_id,
            ).exists()
        )
        if not belongs_to_region:
            raise EditorialWorkflowError(
                code="target_region_mismatch",
                message="O ator não pertence à região editorial informada.",
                status_code=409,
            )
        return Region.objects.get(pk=actor_region_id)
    raise EditorialWorkflowError(
        code="invalid_target_type",
        message="Tipo de alvo editorial inválido.",
        field_errors={"target_type": ["Use region, route ou actor."]},
    )


@transaction.atomic
def create_revision(
    *,
    target_type: str,
    target_id: Any,
    actor_region_id: Any | None,
    snapshot: Any,
    user: Any,
) -> EditorialRevision:
    region = resolve_target_region(
        target_type=target_type,
        target_id=target_id,
        actor_region_id=actor_region_id,
        for_update=True,
    )
    latest = (
        EditorialRevision.objects.filter(target_type=target_type, target_id=target_id)
        .order_by("-sequence")
        .first()
    )
    approved = (
        EditorialRevision.objects.filter(
            target_type=target_type,
            target_id=target_id,
            status=EditorialRevision.Status.APPROVED,
        )
        .order_by("-sequence")
        .first()
    )
    normalized_snapshot = validate_snapshot(snapshot)
    base_snapshot = deepcopy(approved.snapshot) if approved else {}
    return EditorialRevision.objects.create(
        region=region,
        target_type=target_type,
        target_id=target_id,
        sequence=(latest.sequence + 1) if latest else 1,
        base_snapshot=base_snapshot,
        snapshot=normalized_snapshot,
        diff=build_snapshot_diff(base_snapshot, normalized_snapshot),
        created_by=user,
        updated_by=user,
    )


def _save_revision(revision: EditorialRevision) -> EditorialRevision:
    revision.save(
        update_fields=(
            "status",
            "snapshot",
            "diff",
            "lock_version",
            "updated_by",
            "submitted_by",
            "submitted_at",
            "reviewed_by",
            "reviewed_at",
            "return_reason",
            "updated_at",
        )
    )
    return revision


@transaction.atomic
def update_revision(
    *,
    revision_id: Any,
    snapshot: Any,
    expected_lock_version: int,
    user: Any,
) -> EditorialRevision:
    revision = EditorialRevision.objects.select_for_update().get(pk=revision_id)
    apply_snapshot_update(
        revision,
        snapshot=snapshot,
        expected_lock_version=expected_lock_version,
        user=user,
    )
    return _save_revision(revision)


@transaction.atomic
def submit_revision(
    *,
    revision_id: Any,
    expected_lock_version: int,
    user: Any,
) -> EditorialRevision:
    revision = EditorialRevision.objects.select_for_update().get(pk=revision_id)
    apply_submission(
        revision,
        expected_lock_version=expected_lock_version,
        user=user,
    )
    return _save_revision(revision)


@transaction.atomic
def return_revision(
    *,
    revision_id: Any,
    expected_lock_version: int,
    reason: str,
    user: Any,
) -> EditorialRevision:
    revision = EditorialRevision.objects.select_for_update().get(pk=revision_id)
    apply_return(
        revision,
        expected_lock_version=expected_lock_version,
        reason=reason,
        user=user,
    )
    return _save_revision(revision)


@transaction.atomic
def approve_revision(
    *,
    revision_id: Any,
    expected_lock_version: int,
    user: Any,
    request_id: Any = None,
) -> EditorialRevision:
    revision = EditorialRevision.objects.select_for_update().get(pk=revision_id)
    apply_approval(
        revision,
        expected_lock_version=expected_lock_version,
        user=user,
    )
    saved_revision = _save_revision(revision)
    record_audit_event(
        actor=user,
        region=revision.region,
        action=AuditEvent.Action.EDITORIAL_APPROVE,
        target_type="editorial_revision",
        target_id=revision.pk,
        request_id=request_id,
        metadata={
            "content_target_type": revision.target_type,
            "revision_sequence": revision.sequence,
            "change_count": len(revision.diff),
        },
    )
    return saved_revision
