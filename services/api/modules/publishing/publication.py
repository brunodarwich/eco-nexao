from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from modules.audit.models import AuditEvent
from modules.audit.service import record_audit_event
from modules.catalog.models import Actor, ContactChannel, RouteActor
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Route

from .models import EditorialRevision, PublicationVersion
from .rules import snapshot_checksum
from .workflow import EditorialWorkflowError


@dataclass(frozen=True, slots=True)
class PublicationPolicy:
    fields: frozenset[str]
    required_fields: frozenset[str]
    status_field: str


PUBLICATION_POLICIES: dict[str, PublicationPolicy] = {
    EditorialRevision.TargetType.REGION: PublicationPolicy(
        fields=frozenset(
            {
                "slug",
                "public_name",
                "short_description",
                "timezone",
            }
        ),
        required_fields=frozenset(
            {
                "slug",
                "public_name",
                "short_description",
                "timezone",
            }
        ),
        status_field="status",
    ),
    EditorialRevision.TargetType.ROUTE: PublicationPolicy(
        fields=frozenset(
            {
                "slug",
                "public_name",
                "short_promise",
                "description",
                "duration_minutes",
                "difficulty",
                "estimated_cost_min",
                "estimated_cost_max",
                "transport_modes",
                "preparation_content",
                "accessibility_content",
                "offline_enabled",
            }
        ),
        required_fields=frozenset(
            {
                "slug",
                "public_name",
                "short_promise",
                "description",
                "duration_minutes",
                "difficulty",
                "estimated_cost_min",
                "estimated_cost_max",
                "transport_modes",
                "preparation_content",
                "accessibility_content",
                "offline_enabled",
            }
        ),
        status_field="editorial_status",
    ),
    EditorialRevision.TargetType.ACTOR: PublicationPolicy(
        fields=frozenset(
            {
                "actor_kind",
                "category_id",
                "slug",
                "public_name",
                "short_description",
                "full_description",
                "services",
                "partnership_type",
            }
        ),
        required_fields=frozenset(
            {
                "actor_kind",
                "category_id",
                "slug",
                "public_name",
                "short_description",
                "full_description",
                "services",
                "partnership_type",
            }
        ),
        status_field="editorial_status",
    ),
}


def validate_publication_snapshot(target_type: str, snapshot: dict[str, Any]) -> None:
    policy = PUBLICATION_POLICIES[target_type]
    supplied = frozenset(snapshot)
    unknown = sorted(supplied - policy.fields)
    missing = sorted(policy.required_fields - supplied)
    field_errors: dict[str, list[str]] = {}
    if unknown:
        field_errors["snapshot"] = [f"Campos não publicáveis: {', '.join(unknown)}."]
    if missing:
        field_errors.setdefault("snapshot", []).append(
            f"Campos obrigatórios ausentes: {', '.join(missing)}."
        )
    if field_errors:
        raise EditorialWorkflowError(
            code="invalid_publication_snapshot",
            message="O snapshot aprovado não corresponde ao contrato publicável.",
            field_errors=field_errors,
        )


def validate_publication_confirmations(
    approval_subject: Any,
    *,
    publisher: Any,
    source_confirmed: bool,
    human_confirmed: bool,
    critical_information_current: bool,
    critical_override_reason: str,
) -> str:
    errors: dict[str, list[str]] = {}
    approved_by_id = getattr(approval_subject, "reviewed_by_id", None)
    if approved_by_id is None:
        approved_by_id = approval_subject.approved_by_id
    if approved_by_id == publisher.pk:
        raise EditorialWorkflowError(
            code="publication_segregation_required",
            message="A pessoa que aprovou a revisão não pode publicá-la.",
            status_code=403,
        )
    if not source_confirmed:
        errors["source_confirmed"] = ["Confirme a fonte editorial antes de publicar."]
    if not human_confirmed:
        errors["human_confirmed"] = ["A publicação exige confirmação humana."]
    normalized_override = critical_override_reason.strip()
    if not critical_information_current and len(normalized_override) < 20:
        errors["critical_override_reason"] = [
            "Informação crítica vencida exige justificativa com ao menos 20 caracteres."
        ]
    if errors:
        raise EditorialWorkflowError(
            code="publication_blocked",
            message="A publicação foi bloqueada por validações editoriais.",
            field_errors=errors,
        )
    return normalized_override


def validate_restoration_request(
    source: PublicationVersion,
    *,
    restorer: Any,
    reason: str,
    source_confirmed: bool,
    human_confirmed: bool,
    critical_information_current: bool,
    critical_override_reason: str,
) -> tuple[str, str]:
    if source.approved_by_id == restorer.pk:
        raise EditorialWorkflowError(
            code="restoration_segregation_required",
            message="A pessoa que aprovou a versão de origem não pode restaurá-la.",
            status_code=403,
        )
    normalized_reason = reason.strip()
    if len(normalized_reason) < 20:
        raise EditorialWorkflowError(
            code="restoration_reason_required",
            message="A restauração exige uma justificativa explícita.",
            field_errors={"reason": ["Informe uma justificativa com ao menos 20 caracteres."]},
        )
    normalized_override = validate_publication_confirmations(
        source,
        publisher=restorer,
        source_confirmed=source_confirmed,
        human_confirmed=human_confirmed,
        critical_information_current=critical_information_current,
        critical_override_reason=critical_override_reason,
    )
    return normalized_reason, normalized_override


def apply_snapshot_to_target(
    target: Any,
    *,
    target_type: str,
    snapshot: dict[str, Any],
) -> None:
    validate_publication_snapshot(target_type, snapshot)
    policy = PUBLICATION_POLICIES[target_type]
    for field_name in policy.fields:
        setattr(target, field_name, snapshot[field_name])
    setattr(target, policy.status_field, EditorialStatus.PUBLISHED)
    target.full_clean()


def validate_target_references(
    target: Any,
    *,
    target_type: str,
    region: Region,
) -> None:
    errors: dict[str, list[str]] = {}
    if target_type == EditorialRevision.TargetType.REGION:
        if target.center_point is None:
            errors["center_point"] = ["A região exige um centro geográfico."]
    elif target_type == EditorialRevision.TargetType.ROUTE:
        if target.region.status != EditorialStatus.PUBLISHED:
            errors["region"] = ["A região da rota ainda não está publicada."]
        if not target.stages.exists():
            errors["stages"] = ["A rota exige ao menos uma etapa."]
        invalid_actors = RouteActor.objects.filter(route=target).exclude(
            actor__editorial_status=EditorialStatus.PUBLISHED,
            actor__category__is_active=True,
        )
        if invalid_actors.exists():
            errors["actors"] = [
                "Todos os atores relacionados devem estar publicados e com categoria ativa."
            ]
    elif target_type == EditorialRevision.TargetType.ACTOR:
        if not target.category.is_active:
            errors["category_id"] = ["A categoria do ator está inativa."]
        if not target.locations.filter(region=region).exists():
            errors["region"] = ["O ator não possui localização na região editorial."]
        invalid_contacts = ContactChannel.objects.filter(
            actor=target,
            is_public=True,
        ).filter(
            Q(public_value="")
            | Q(source_reference="")
            | Q(verified_at__isnull=True)
            | Q(verified_by__isnull=True)
        )
        if invalid_contacts.exists():
            errors["contacts"] = [
                "Contatos públicos exigem valor, autorização e verificação vigente."
            ]
    if errors:
        raise EditorialWorkflowError(
            code="publication_references_invalid",
            message="A publicação referencia conteúdo incompleto ou não publicado.",
            field_errors=errors,
        )


def _locked_target_for(*, target_type: str, target_id: Any) -> Any:
    if target_type == EditorialRevision.TargetType.REGION:
        return Region.objects.select_for_update().get(pk=target_id)
    if target_type == EditorialRevision.TargetType.ROUTE:
        return Route.objects.select_for_update().select_related("region").get(pk=target_id)
    if target_type == EditorialRevision.TargetType.ACTOR:
        return Actor.objects.select_for_update().select_related("category").get(pk=target_id)
    raise EditorialWorkflowError(
        code="invalid_target_type",
        message="Tipo de alvo editorial inválido.",
    )


def _locked_target(revision: EditorialRevision) -> Any:
    return _locked_target_for(
        target_type=revision.target_type,
        target_id=revision.target_id,
    )


@transaction.atomic
def publish_revision(
    *,
    revision_id: Any,
    expected_lock_version: int,
    publisher: Any,
    reason: str,
    source_confirmed: bool,
    human_confirmed: bool,
    critical_information_current: bool,
    critical_override_reason: str,
    request_id: Any = None,
) -> PublicationVersion:
    revision = (
        EditorialRevision.objects.select_for_update()
        .select_related("region", "reviewed_by")
        .get(pk=revision_id)
    )
    existing = PublicationVersion.objects.filter(revision=revision).first()
    if existing:
        return existing
    if revision.status != EditorialRevision.Status.APPROVED:
        raise EditorialWorkflowError(
            code="invalid_revision_state",
            message="Somente uma revisão aprovada pode ser publicada.",
            status_code=409,
        )
    if revision.lock_version != expected_lock_version:
        raise EditorialWorkflowError(
            code="revision_conflict",
            message="A revisão foi alterada por outra operação.",
            status_code=409,
            field_errors={"lock_version": ["Recarregue a revisão antes de publicar."]},
        )
    if revision.reviewed_by is None:
        raise EditorialWorkflowError(
            code="review_required",
            message="A publicação exige aprovação identificada.",
            status_code=409,
        )
    normalized_override = validate_publication_confirmations(
        revision,
        publisher=publisher,
        source_confirmed=source_confirmed,
        human_confirmed=human_confirmed,
        critical_information_current=critical_information_current,
        critical_override_reason=critical_override_reason,
    )

    target = _locked_target(revision)
    apply_snapshot_to_target(
        target,
        target_type=revision.target_type,
        snapshot=revision.snapshot,
    )
    validate_target_references(
        target,
        target_type=revision.target_type,
        region=revision.region,
    )
    latest = (
        PublicationVersion.objects.filter(
            target_type=revision.target_type,
            target_id=revision.target_id,
        )
        .order_by("-version")
        .first()
    )
    version_number = latest.version + 1 if latest else 1
    if revision.target_type == EditorialRevision.TargetType.REGION:
        target.published_version = version_number
    target.save()

    published_at = timezone.now()
    publication = PublicationVersion.objects.create(
        revision=revision,
        region=revision.region,
        target_type=revision.target_type,
        target_id=revision.target_id,
        version=version_number,
        snapshot=revision.snapshot,
        checksum=snapshot_checksum(revision.snapshot),
        approved_by=revision.reviewed_by,
        published_by=publisher,
        reason=reason.strip(),
        source_confirmed=source_confirmed,
        human_confirmed=human_confirmed,
        critical_information_current=critical_information_current,
        critical_override_reason=normalized_override,
        published_at=published_at,
    )
    revision.status = EditorialRevision.Status.PUBLISHED
    revision.updated_by = publisher
    revision.lock_version += 1
    revision.save(update_fields=("status", "updated_by", "lock_version", "updated_at"))
    record_audit_event(
        actor=publisher,
        region=revision.region,
        action=AuditEvent.Action.PUBLICATION_PUBLISH,
        target_type="publication_version",
        target_id=publication.pk,
        request_id=request_id,
        reason=publication.reason,
        metadata={
            "content_target_type": publication.target_type,
            "content_target_id": str(publication.target_id),
            "publication_id": str(publication.pk),
            "version": publication.version,
            "checksum": publication.checksum,
            "critical_override": not publication.critical_information_current,
        },
    )
    return publication


@transaction.atomic
def restore_publication(
    *,
    source_publication_id: Any,
    expected_current_version: int,
    restorer: Any,
    reason: str,
    source_confirmed: bool,
    human_confirmed: bool,
    critical_information_current: bool,
    critical_override_reason: str,
    request_id: Any = None,
) -> PublicationVersion:
    source = PublicationVersion.objects.select_related("region", "approved_by").get(
        pk=source_publication_id
    )
    target = _locked_target_for(
        target_type=source.target_type,
        target_id=source.target_id,
    )
    current = (
        PublicationVersion.objects.select_for_update()
        .filter(
            target_type=source.target_type,
            target_id=source.target_id,
        )
        .order_by("-version")
        .first()
    )
    if current is None or current.version != expected_current_version:
        raise EditorialWorkflowError(
            code="publication_conflict",
            message="O conteúdo recebeu outra publicação.",
            status_code=409,
            field_errors={
                "expected_current_version": ["Recarregue o histórico antes de restaurar."]
            },
        )
    if current.pk == source.pk:
        raise EditorialWorkflowError(
            code="current_version_restore_forbidden",
            message="A versão pública atual não precisa ser restaurada.",
            status_code=409,
        )

    normalized_reason, normalized_override = validate_restoration_request(
        source,
        restorer=restorer,
        reason=reason,
        source_confirmed=source_confirmed,
        human_confirmed=human_confirmed,
        critical_information_current=critical_information_current,
        critical_override_reason=critical_override_reason,
    )
    snapshot = deepcopy(source.snapshot)
    apply_snapshot_to_target(
        target,
        target_type=source.target_type,
        snapshot=snapshot,
    )
    validate_target_references(
        target,
        target_type=source.target_type,
        region=source.region,
    )
    version_number = current.version + 1
    if source.target_type == EditorialRevision.TargetType.REGION:
        target.published_version = version_number
    target.save()

    publication = PublicationVersion.objects.create(
        revision=None,
        restored_from=source,
        region=source.region,
        target_type=source.target_type,
        target_id=source.target_id,
        version=version_number,
        snapshot=snapshot,
        checksum=snapshot_checksum(snapshot),
        approved_by=source.approved_by,
        published_by=restorer,
        reason=normalized_reason,
        source_confirmed=source_confirmed,
        human_confirmed=human_confirmed,
        critical_information_current=critical_information_current,
        critical_override_reason=normalized_override,
        published_at=timezone.now(),
    )
    record_audit_event(
        actor=restorer,
        region=source.region,
        action=AuditEvent.Action.PUBLICATION_RESTORE,
        target_type="publication_version",
        target_id=publication.pk,
        request_id=request_id,
        reason=publication.reason,
        metadata={
            "content_target_type": publication.target_type,
            "content_target_id": str(publication.target_id),
            "publication_id": str(publication.pk),
            "source_publication_id": str(source.pk),
            "version": publication.version,
            "source_version": source.version,
            "checksum": publication.checksum,
            "critical_override": not publication.critical_information_current,
        },
    )
    return publication
