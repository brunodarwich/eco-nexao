import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from drf_spectacular.generators import SchemaGenerator

from modules.accounts.permissions import AdminAction

from .models import EditorialRevision
from .views import (
    EditorialRevisionApproveView,
    EditorialRevisionCreateView,
    EditorialRevisionReturnView,
)
from .workflow import (
    MAX_SNAPSHOT_BYTES,
    EditorialWorkflowError,
    apply_approval,
    apply_return,
    apply_snapshot_update,
    apply_submission,
    approve_revision,
    build_snapshot_diff,
    validate_snapshot,
)


def revision(*, status=EditorialRevision.Status.DRAFT, lock_version=1):
    return SimpleNamespace(
        base_snapshot={"name": "Antes", "obsolete": True},
        diff=[],
        lock_version=lock_version,
        return_reason="",
        reviewed_at=None,
        reviewed_by=None,
        snapshot={"name": "Antes", "obsolete": True},
        status=status,
        submitted_at=None,
        submitted_by=None,
        submitted_by_id=None,
        updated_by=None,
    )


def user(pk: int):
    return SimpleNamespace(pk=pk)


def test_snapshot_diff_is_deterministic_and_uses_escaped_json_pointers():
    before = {"name": "Antes", "nested": {"a/b": 1}, "remove": True}
    after = {"add": "novo", "name": "Depois", "nested": {"a/b": 2}}

    assert build_snapshot_diff(before, after) == [
        {"operation": "add", "path": "/add", "before": None, "after": "novo"},
        {
            "operation": "replace",
            "path": "/name",
            "before": "Antes",
            "after": "Depois",
        },
        {
            "operation": "replace",
            "path": "/nested/a~1b",
            "before": 1,
            "after": 2,
        },
        {"operation": "remove", "path": "/remove", "before": True, "after": None},
    ]


def test_snapshot_requires_json_object_and_enforces_size_limit():
    with pytest.raises(EditorialWorkflowError) as invalid:
        validate_snapshot(["não", "é", "objeto"])
    assert invalid.value.code == "invalid_snapshot"

    oversized = {"content": "a" * MAX_SNAPSHOT_BYTES}
    with pytest.raises(EditorialWorkflowError) as too_large:
        validate_snapshot(oversized)
    assert too_large.value.code == "snapshot_too_large"
    assert too_large.value.status_code == 413


def test_draft_update_recalculates_diff_and_advances_optimistic_lock():
    draft = revision()
    editor = user(1)

    apply_snapshot_update(
        draft,
        snapshot={"name": "Depois"},
        expected_lock_version=1,
        user=editor,
    )

    assert draft.snapshot == {"name": "Depois"}
    assert draft.diff == [
        {
            "operation": "replace",
            "path": "/name",
            "before": "Antes",
            "after": "Depois",
        },
        {"operation": "remove", "path": "/obsolete", "before": True, "after": None},
    ]
    assert draft.lock_version == 2
    assert draft.updated_by is editor


def test_stale_lock_and_non_draft_edits_are_rejected():
    draft = revision(lock_version=3)
    with pytest.raises(EditorialWorkflowError) as conflict:
        apply_snapshot_update(
            draft,
            snapshot={"name": "Conflito"},
            expected_lock_version=2,
            user=user(1),
        )
    assert conflict.value.code == "revision_conflict"
    assert conflict.value.status_code == 409

    approved = revision(status=EditorialRevision.Status.APPROVED)
    with pytest.raises(EditorialWorkflowError) as immutable:
        apply_snapshot_update(
            approved,
            snapshot={"name": "Alteração"},
            expected_lock_version=1,
            user=user(1),
        )
    assert immutable.value.code == "invalid_revision_state"


def test_submit_return_and_resubmit_preserve_controlled_states():
    item = revision()
    editor = user(1)
    reviewer = user(2)

    apply_submission(item, expected_lock_version=1, user=editor)
    assert item.status == EditorialRevision.Status.REVIEW
    assert item.submitted_by is editor
    assert item.lock_version == 2

    with pytest.raises(EditorialWorkflowError) as missing_reason:
        apply_return(
            item,
            expected_lock_version=2,
            reason="  ",
            user=reviewer,
        )
    assert missing_reason.value.code == "return_reason_required"

    apply_return(
        item,
        expected_lock_version=2,
        reason="  Atualize a fonte.  ",
        user=reviewer,
    )
    assert item.status == EditorialRevision.Status.DRAFT
    assert item.return_reason == "Atualize a fonte."
    assert item.reviewed_by is reviewer
    assert item.lock_version == 3

    apply_submission(item, expected_lock_version=3, user=editor)
    assert item.status == EditorialRevision.Status.REVIEW
    assert item.lock_version == 4


def test_submitter_cannot_approve_own_revision():
    reviewer = user(2)
    item = revision(status=EditorialRevision.Status.REVIEW)
    item.submitted_by_id = reviewer.pk

    with pytest.raises(EditorialWorkflowError) as segregation:
        apply_approval(
            item,
            expected_lock_version=1,
            user=reviewer,
        )

    assert segregation.value.code == "review_segregation_required"
    assert segregation.value.status_code == 403
    assert item.status == EditorialRevision.Status.REVIEW


def test_different_reviewer_can_approve():
    item = revision(status=EditorialRevision.Status.REVIEW)
    item.submitted_by_id = 1
    reviewer = user(2)

    apply_approval(item, expected_lock_version=1, user=reviewer)

    assert item.status == EditorialRevision.Status.APPROVED
    assert item.reviewed_by is reviewer
    assert item.lock_version == 2


def test_approval_service_records_minimized_audit_in_same_transaction():
    reviewer = user(2)
    item = SimpleNamespace(
        pk=uuid4(),
        region=SimpleNamespace(pk=uuid4()),
        target_type=EditorialRevision.TargetType.ROUTE,
        sequence=4,
        diff=[{"operation": "replace"}, {"operation": "add"}],
    )
    queryset = MagicMock()
    queryset.get.return_value = item
    request_id = uuid4()

    with (
        patch(
            "modules.publishing.workflow.EditorialRevision.objects.select_for_update",
            return_value=queryset,
        ),
        patch("modules.publishing.workflow.apply_approval"),
        patch(
            "modules.publishing.workflow._save_revision",
            return_value=item,
        ),
        patch("modules.publishing.workflow.record_audit_event") as record_audit,
    ):
        result = approve_revision.__wrapped__(
            revision_id=item.pk,
            expected_lock_version=1,
            user=reviewer,
            request_id=request_id,
        )

    assert result is item
    audit = record_audit.call_args.kwargs
    assert audit["request_id"] == request_id
    assert audit["target_id"] == item.pk
    assert audit["metadata"] == {
        "content_target_type": EditorialRevision.TargetType.ROUTE,
        "revision_sequence": 4,
        "change_count": 2,
    }


def test_revision_model_declares_sequence_and_lock_constraints():
    constraint_names = {constraint.name for constraint in EditorialRevision._meta.constraints}
    assert {
        "revision_target_sequence_uniq",
        "revision_sequence_positive",
        "revision_lock_version_positive",
    } <= constraint_names


def test_editorial_endpoints_are_session_protected_and_action_specific():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    paths = {
        "/api/v1/admin/editorial/revisions",
        "/api/v1/admin/editorial/revisions/{revision_id}",
        "/api/v1/admin/editorial/revisions/{revision_id}/submit",
        "/api/v1/admin/editorial/revisions/{revision_id}/return",
        "/api/v1/admin/editorial/revisions/{revision_id}/approve",
        "/api/v1/admin/editorial/revisions/{revision_id}/publish",
    }

    assert paths <= schema["paths"].keys()
    for path in paths:
        for operation in schema["paths"][path].values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            assert operation.get("security") == [{"cookieAuth": []}]

    assert EditorialRevisionCreateView.required_admin_action == AdminAction.EDIT_CONTENT
    assert EditorialRevisionReturnView.required_admin_action == AdminAction.APPROVE
    assert EditorialRevisionApproveView.required_admin_action == AdminAction.APPROVE
    assert "base_snapshot" in json.dumps(schema["components"]["schemas"])
