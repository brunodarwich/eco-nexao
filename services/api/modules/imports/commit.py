from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from django.db import IntegrityError, transaction

from modules.audit.models import AuditEvent
from modules.audit.service import record_audit_event
from modules.catalog.models import Actor
from modules.regions.models import Region

from .catalog_csv import CatalogRelationIndex, validate_catalog_csv
from .models import CatalogImportBatch, CatalogImportDraft


@dataclass(frozen=True, slots=True)
class CatalogImportCommitError(Exception):
    code: str
    message: str
    status_code: int = 400
    field_errors: dict[str, list[str]] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class CatalogImportCommitResult:
    batch: CatalogImportBatch
    replayed: bool


def _existing_batch(
    *,
    sha256: str,
    idempotency_key: UUID,
    user: Any,
) -> CatalogImportBatch | None:
    by_key = CatalogImportBatch.objects.filter(idempotency_key=idempotency_key).first()
    if by_key is not None:
        if by_key.sha256 == sha256 and by_key.created_by_id == user.pk:
            return by_key
        raise CatalogImportCommitError(
            code="import_idempotency_conflict",
            message="A confirmação conflita com um lote já registrado.",
            status_code=409,
        )
    by_hash = CatalogImportBatch.objects.filter(sha256=sha256).first()
    if by_hash is not None:
        if by_hash.created_by_id == user.pk:
            return by_hash
        raise CatalogImportCommitError(
            code="import_file_already_committed",
            message="O arquivo já foi confirmado em outro lote.",
            status_code=409,
        )
    return None


@transaction.atomic
def commit_catalog_import(
    *,
    content: bytes,
    original_filename: str,
    expected_sha256: str,
    idempotency_key: UUID,
    user: Any,
    relations: CatalogRelationIndex,
    request_id: UUID | str | None,
) -> CatalogImportCommitResult:
    result = validate_catalog_csv(content, relations)
    if result.sha256 != expected_sha256:
        raise CatalogImportCommitError(
            code="import_hash_mismatch",
            message="O arquivo não corresponde à prévia confirmada.",
            status_code=409,
            field_errors={"sha256": ["Envie novamente o arquivo validado."]},
        )
    if not result.valid:
        raise CatalogImportCommitError(
            code="import_validation_failed",
            message="O arquivo deixou de atender aos critérios de importação.",
            status_code=400,
            field_errors={"file": ["Execute a pré-validação novamente e corrija os erros."]},
        )

    existing = _existing_batch(
        sha256=result.sha256,
        idempotency_key=idempotency_key,
        user=user,
    )
    if existing is not None:
        return CatalogImportCommitResult(existing, replayed=True)

    preview_by_line = {row.line: row for row in result.preview_rows}
    operations = [row.operation for row in result.preview_rows]
    region_slugs = {row["region_slug"] for row in result.normalized_rows}
    regions = {
        region.slug: region
        for region in Region.objects.select_for_update().filter(slug__in=region_slugs)
    }
    actor_ids = {row.external_id for row in result.preview_rows if row.operation != "create"}
    actors = {
        actor.external_id: actor
        for actor in Actor.objects.select_for_update().filter(external_id__in=actor_ids)
    }
    if set(regions) != region_slugs or set(actors) != actor_ids:
        raise CatalogImportCommitError(
            code="import_relations_changed",
            message="As relações do catálogo mudaram desde a prévia.",
            status_code=409,
        )

    try:
        batch = CatalogImportBatch.objects.create(
            idempotency_key=idempotency_key,
            sha256=result.sha256,
            original_filename=original_filename[:255],
            byte_size=len(content),
            row_count=result.row_count,
            warning_count=result.warning_count,
            create_count=operations.count("create"),
            update_count=operations.count("update"),
            archive_count=operations.count("archive"),
            created_by=user,
        )
    except IntegrityError as error:
        raise CatalogImportCommitError(
            code="import_commit_conflict",
            message="Outro processo confirmou este lote simultaneamente.",
            status_code=409,
        ) from error

    drafts = []
    for line_number, payload in enumerate(result.normalized_rows, start=2):
        preview = preview_by_line[line_number]
        drafts.append(
            CatalogImportDraft(
                batch=batch,
                line_number=line_number,
                region=regions[payload["region_slug"]],
                external_id=payload["external_id"],
                operation=preview.operation,
                target_actor=actors.get(payload["external_id"]),
                payload=payload,
            )
        )
    CatalogImportDraft.objects.bulk_create(drafts)
    record_audit_event(
        actor=user,
        action=AuditEvent.Action.IMPORT_COMMIT,
        target_type="catalog_import_batch",
        target_id=batch.pk,
        request_id=request_id,
        metadata={
            "sha256": batch.sha256,
            "row_count": batch.row_count,
            "warning_count": batch.warning_count,
            "create_count": batch.create_count,
            "update_count": batch.update_count,
            "archive_count": batch.archive_count,
        },
    )
    return CatalogImportCommitResult(batch, replayed=False)
