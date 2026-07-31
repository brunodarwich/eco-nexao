from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from modules.audit.models import AuditEvent

from .catalog_csv import (
    CatalogCsvValidationResult,
    CatalogPreviewRow,
)
from .commit import CatalogImportCommitError, commit_catalog_import
from .models import CatalogImportBatch, CatalogImportDraft


def valid_result() -> CatalogCsvValidationResult:
    return CatalogCsvValidationResult(
        sha256="a" * 64,
        row_count=2,
        issues=(),
        preview_rows=(
            CatalogPreviewRow(line=2, external_id="source:new", operation="create"),
            CatalogPreviewRow(line=3, external_id="source:current", operation="update"),
        ),
        normalized_rows=(
            {
                "external_id": "source:new",
                "region_slug": "region-a",
                "public_name": "Novo",
            },
            {
                "external_id": "source:current",
                "region_slug": "region-a",
                "public_name": "Atualizado",
            },
        ),
    )


def test_commit_persists_private_drafts_and_minimized_audit_atomically():
    result = valid_result()
    user = SimpleNamespace(pk=7)
    region = SimpleNamespace(slug="region-a")
    actor = SimpleNamespace(external_id="source:current")
    batch = SimpleNamespace(
        pk=uuid4(),
        sha256=result.sha256,
        row_count=2,
        warning_count=0,
        create_count=1,
        update_count=1,
        archive_count=0,
    )
    batch_filter = MagicMock()
    batch_filter.first.return_value = None
    batch_manager = MagicMock()
    batch_manager.filter.return_value = batch_filter
    batch_manager.create.return_value = batch
    region_queryset = MagicMock()
    region_queryset.filter.return_value = [region]
    actor_queryset = MagicMock()
    actor_queryset.filter.return_value = [actor]
    created_drafts = []

    def capture_draft(**kwargs):
        created_drafts.append(kwargs)
        return SimpleNamespace(**kwargs)

    with (
        patch("modules.imports.commit.validate_catalog_csv", return_value=result),
        patch("modules.imports.commit.CatalogImportBatch.objects", batch_manager),
        patch(
            "modules.imports.commit.Region.objects.select_for_update",
            return_value=region_queryset,
        ),
        patch(
            "modules.imports.commit.Actor.objects.select_for_update",
            return_value=actor_queryset,
        ),
        patch("modules.imports.commit.CatalogImportDraft", side_effect=capture_draft),
        patch("modules.imports.commit.CatalogImportDraft.objects.bulk_create") as bulk_create,
        patch("modules.imports.commit.record_audit_event") as record_audit,
    ):
        committed = commit_catalog_import.__wrapped__(
            content=b"csv",
            original_filename="catalog.csv",
            expected_sha256=result.sha256,
            idempotency_key=uuid4(),
            user=user,
            relations=SimpleNamespace(),
            request_id=uuid4(),
        )

    assert committed.batch is batch
    assert committed.replayed is False
    assert [draft["operation"] for draft in created_drafts] == ["create", "update"]
    assert created_drafts[0]["target_actor"] is None
    assert created_drafts[1]["target_actor"] is actor
    assert created_drafts[0]["payload"]["public_name"] == "Novo"
    bulk_create.assert_called_once()
    audit = record_audit.call_args.kwargs
    assert audit["action"] == AuditEvent.Action.IMPORT_COMMIT
    assert audit["target_id"] == batch.pk
    assert audit["metadata"] == {
        "sha256": result.sha256,
        "row_count": 2,
        "warning_count": 0,
        "create_count": 1,
        "update_count": 1,
        "archive_count": 0,
    }
    assert "public_name" not in str(audit)


def test_commit_replay_returns_existing_batch_without_duplicate_writes_or_audit():
    result = valid_result()
    user = SimpleNamespace(pk=7)
    existing = SimpleNamespace(
        sha256=result.sha256,
        created_by_id=user.pk,
    )
    batch_queryset = MagicMock()
    batch_queryset.first.return_value = existing

    with (
        patch("modules.imports.commit.validate_catalog_csv", return_value=result),
        patch(
            "modules.imports.commit.CatalogImportBatch.objects.filter",
            return_value=batch_queryset,
        ) as batch_filter,
        patch("modules.imports.commit.CatalogImportDraft.objects.bulk_create") as bulk_create,
        patch("modules.imports.commit.record_audit_event") as audit,
    ):
        replay = commit_catalog_import.__wrapped__(
            content=b"csv",
            original_filename="catalog.csv",
            expected_sha256=result.sha256,
            idempotency_key=uuid4(),
            user=user,
            relations=SimpleNamespace(),
            request_id=uuid4(),
        )

    assert replay.batch is existing
    assert replay.replayed is True
    assert batch_filter.call_count == 1
    bulk_create.assert_not_called()
    audit.assert_not_called()


def test_commit_rejects_hash_mismatch_before_any_persistence():
    result = valid_result()

    with (
        patch("modules.imports.commit.validate_catalog_csv", return_value=result),
        patch("modules.imports.commit.CatalogImportBatch.objects.create") as create_batch,
        pytest.raises(CatalogImportCommitError) as mismatch,
    ):
        commit_catalog_import.__wrapped__(
            content=b"changed",
            original_filename="catalog.csv",
            expected_sha256="b" * 64,
            idempotency_key=uuid4(),
            user=SimpleNamespace(pk=7),
            relations=SimpleNamespace(),
            request_id=uuid4(),
        )

    assert mismatch.value.code == "import_hash_mismatch"
    assert mismatch.value.status_code == 409
    create_batch.assert_not_called()


def test_import_models_enforce_idempotency_and_draft_constraints():
    assert CatalogImportBatch._meta.get_field("sha256").unique
    assert CatalogImportBatch._meta.get_field("idempotency_key").unique
    constraint_names = {constraint.name for constraint in CatalogImportDraft._meta.constraints}
    assert {
        "import_draft_batch_line_uniq",
        "import_draft_batch_external_uniq",
        "import_draft_line_valid",
    } <= constraint_names
