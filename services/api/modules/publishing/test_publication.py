from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from drf_spectacular.generators import SchemaGenerator

from modules.accounts.permissions import AdminAction
from modules.audit.models import AuditEvent
from modules.core.models import EditorialStatus

from .models import EditorialRevision, PublicationVersion
from .publication import (
    PUBLICATION_POLICIES,
    apply_snapshot_to_target,
    publish_revision,
    restore_publication,
    validate_publication_confirmations,
    validate_publication_snapshot,
    validate_restoration_request,
    validate_target_references,
)
from .views import EditorialRevisionPublishView, PublicationVersionRestoreView
from .workflow import EditorialWorkflowError


def approved_revision(*, reviewer_id=2):
    return SimpleNamespace(reviewed_by_id=reviewer_id)


def test_publication_snapshots_use_complete_explicit_allowlists():
    for target_type, policy in PUBLICATION_POLICIES.items():
        snapshot = dict.fromkeys(policy.required_fields, "value")
        validate_publication_snapshot(target_type, snapshot)

        with pytest.raises(EditorialWorkflowError) as private_field:
            validate_publication_snapshot(
                target_type,
                {**snapshot, "legal_name": "Não deve publicar"},
            )
        assert private_field.value.code == "invalid_publication_snapshot"
        assert "legal_name" in private_field.value.field_errors["snapshot"][0]

        missing_field = next(iter(policy.required_fields))
        with pytest.raises(EditorialWorkflowError) as incomplete:
            validate_publication_snapshot(
                target_type,
                {key: value for key, value in snapshot.items() if key != missing_field},
            )
        assert missing_field in " ".join(incomplete.value.field_errors["snapshot"])


def test_publication_requires_source_human_confirmation_and_segregation():
    revision = approved_revision()
    publisher = SimpleNamespace(pk=3)

    with pytest.raises(EditorialWorkflowError) as blocked:
        validate_publication_confirmations(
            revision,
            publisher=publisher,
            source_confirmed=False,
            human_confirmed=False,
            critical_information_current=True,
            critical_override_reason="",
        )
    assert blocked.value.code == "publication_blocked"
    assert set(blocked.value.field_errors) == {
        "source_confirmed",
        "human_confirmed",
    }

    with pytest.raises(EditorialWorkflowError) as segregation:
        validate_publication_confirmations(
            revision,
            publisher=SimpleNamespace(pk=2),
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=True,
            critical_override_reason="",
        )
    assert segregation.value.code == "publication_segregation_required"
    assert segregation.value.status_code == 403


def test_expired_critical_information_needs_recorded_override():
    revision = approved_revision()
    publisher = SimpleNamespace(pk=3)

    with pytest.raises(EditorialWorkflowError) as blocked:
        validate_publication_confirmations(
            revision,
            publisher=publisher,
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=False,
            critical_override_reason="muito curta",
        )
    assert "critical_override_reason" in blocked.value.field_errors

    reason = validate_publication_confirmations(
        revision,
        publisher=publisher,
        source_confirmed=True,
        human_confirmed=True,
        critical_information_current=False,
        critical_override_reason="  Publicação emergencial confirmada pelo responsável.  ",
    )
    assert reason == "Publicação emergencial confirmada pelo responsável."


def test_snapshot_application_sets_public_state_and_runs_model_validation():
    target = SimpleNamespace(full_clean=MagicMock())
    snapshot = {
        "slug": "regiao-a",
        "public_name": "Região A",
        "short_description": "Descrição verificada.",
        "timezone": "America/Fortaleza",
    }

    apply_snapshot_to_target(
        target,
        target_type=EditorialRevision.TargetType.REGION,
        snapshot=snapshot,
    )

    assert target.status == EditorialStatus.PUBLISHED
    assert target.public_name == "Região A"
    target.full_clean.assert_called_once_with()


def test_route_publication_blocks_unpublished_region_empty_stages_and_actors():
    target = SimpleNamespace(
        region=SimpleNamespace(status=EditorialStatus.DRAFT),
        stages=SimpleNamespace(exists=lambda: False),
    )
    invalid_links = MagicMock()
    invalid_links.exclude.return_value.exists.return_value = True

    with (
        patch(
            "modules.publishing.publication.RouteActor.objects.filter",
            return_value=invalid_links,
        ),
        pytest.raises(EditorialWorkflowError) as blocked,
    ):
        validate_target_references(
            target,
            target_type=EditorialRevision.TargetType.ROUTE,
            region=SimpleNamespace(),
        )

    assert set(blocked.value.field_errors) == {"region", "stages", "actors"}


def test_actor_publication_blocks_inactive_category_region_and_contacts():
    target = SimpleNamespace(
        category=SimpleNamespace(is_active=False),
        locations=SimpleNamespace(filter=lambda **_kwargs: SimpleNamespace(exists=lambda: False)),
    )
    invalid_contacts = MagicMock()
    invalid_contacts.filter.return_value.exists.return_value = True

    with (
        patch(
            "modules.publishing.publication.ContactChannel.objects.filter",
            return_value=invalid_contacts,
        ),
        pytest.raises(EditorialWorkflowError) as blocked,
    ):
        validate_target_references(
            target,
            target_type=EditorialRevision.TargetType.ACTOR,
            region=SimpleNamespace(pk="region-a"),
        )

    assert set(blocked.value.field_errors) == {
        "category_id",
        "region",
        "contacts",
    }


def test_publication_models_enforce_immutable_sequence_and_single_revision():
    constraint_names = {constraint.name for constraint in PublicationVersion._meta.constraints}
    assert {
        "publication_target_version_uniq",
        "publication_version_positive",
    } <= constraint_names
    assert PublicationVersion._meta.get_field("revision").one_to_one is True
    assert EditorialRevision.Status.PUBLISHED == "published"


def test_publish_service_and_endpoint_are_atomic_and_publisher_only():
    assert hasattr(publish_revision, "__wrapped__")
    assert EditorialRevisionPublishView.required_admin_action == AdminAction.PUBLISH

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/admin/editorial/revisions/{revision_id}/publish"]["post"]
    assert operation["operationId"] == "publishEditorialRevision"
    assert operation["security"] == [{"cookieAuth": []}]


def test_publish_service_records_minimized_audit_event():
    publisher = SimpleNamespace(pk=3)
    reviewer = SimpleNamespace(pk=2)
    region = SimpleNamespace(pk="region-a")
    revision = SimpleNamespace(
        pk="revision-a",
        status=EditorialRevision.Status.APPROVED,
        lock_version=3,
        reviewed_by=reviewer,
        reviewed_by_id=reviewer.pk,
        region=region,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-a",
        snapshot={"slug": "rota-a"},
        save=MagicMock(),
    )
    target = MagicMock()
    existing_query = MagicMock()
    existing_query.first.return_value = None
    latest_query = MagicMock()
    latest_query.order_by.return_value.first.return_value = None
    revision_query = MagicMock()
    revision_query.select_related.return_value.get.return_value = revision
    publication = SimpleNamespace(
        pk="publication-a",
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-a",
        version=1,
        checksum="a" * 64,
        reason="Publicação inicial validada.",
        critical_information_current=False,
    )
    request_id = "7c3f1ca8-7964-4f06-99bf-8187ecdb2743"

    with (
        patch(
            "modules.publishing.publication.EditorialRevision.objects.select_for_update",
            return_value=revision_query,
        ),
        patch(
            "modules.publishing.publication.PublicationVersion.objects.filter",
            side_effect=[existing_query, latest_query],
        ),
        patch(
            "modules.publishing.publication.validate_publication_confirmations",
            return_value="Exceção crítica confirmada pela operação.",
        ),
        patch(
            "modules.publishing.publication._locked_target",
            return_value=target,
        ),
        patch("modules.publishing.publication.apply_snapshot_to_target"),
        patch("modules.publishing.publication.validate_target_references"),
        patch(
            "modules.publishing.publication.PublicationVersion.objects.create",
            return_value=publication,
        ),
        patch("modules.publishing.publication.record_audit_event") as record_audit,
    ):
        result = publish_revision.__wrapped__(
            revision_id=revision.pk,
            expected_lock_version=3,
            publisher=publisher,
            reason="Publicação inicial validada.",
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=False,
            critical_override_reason="Exceção crítica confirmada pela operação.",
            request_id=request_id,
        )

    assert result is publication
    audit = record_audit.call_args.kwargs
    assert audit["action"] == AuditEvent.Action.PUBLICATION_PUBLISH
    assert audit["request_id"] == request_id
    assert audit["metadata"] == {
        "content_target_type": EditorialRevision.TargetType.ROUTE,
        "content_target_id": "route-a",
        "publication_id": "publication-a",
        "version": 1,
        "checksum": "a" * 64,
        "critical_override": True,
    }


def test_restoration_requires_reason_confirmations_and_segregation():
    source = SimpleNamespace(approved_by_id=2)
    restorer = SimpleNamespace(pk=3)

    with pytest.raises(EditorialWorkflowError) as short_reason:
        validate_restoration_request(
            source,
            restorer=restorer,
            reason="curta",
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=True,
            critical_override_reason="",
        )
    assert short_reason.value.code == "restoration_reason_required"

    with pytest.raises(EditorialWorkflowError) as segregation:
        validate_restoration_request(
            source,
            restorer=SimpleNamespace(pk=2),
            reason="Restaurar conteúdo validado anteriormente.",
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=True,
            critical_override_reason="",
        )
    assert segregation.value.code == "restoration_segregation_required"
    assert segregation.value.status_code == 403

    reason, override = validate_restoration_request(
        source,
        restorer=restorer,
        reason="  Restaurar conteúdo validado anteriormente.  ",
        source_confirmed=True,
        human_confirmed=True,
        critical_information_current=True,
        critical_override_reason="",
    )
    assert reason == "Restaurar conteúdo validado anteriormente."
    assert override == ""


def test_restore_service_reapplies_snapshot_and_creates_next_version():
    source = SimpleNamespace(
        pk="source-version",
        approved_by_id=2,
        approved_by=SimpleNamespace(pk=2),
        region=SimpleNamespace(pk="region-a"),
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-a",
        snapshot={"slug": "rota-restaurada"},
        version=2,
    )
    current = SimpleNamespace(pk="current-version", version=4)
    locked = MagicMock()
    source_query = MagicMock()
    source_query.get.return_value = source
    current_query = MagicMock()
    current_query.filter.return_value.order_by.return_value.first.return_value = current
    created = SimpleNamespace(
        pk="restored-version",
        version=5,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-a",
        checksum="a" * 64,
        reason="Restaurar conteúdo validado anteriormente.",
        critical_information_current=True,
    )

    with (
        patch(
            "modules.publishing.publication.PublicationVersion.objects.select_related",
            return_value=source_query,
        ),
        patch(
            "modules.publishing.publication.PublicationVersion.objects.select_for_update",
            return_value=current_query,
        ),
        patch(
            "modules.publishing.publication._locked_target_for",
            return_value=locked,
        ),
        patch("modules.publishing.publication.apply_snapshot_to_target") as apply_snapshot,
        patch("modules.publishing.publication.validate_target_references") as validate_references,
        patch(
            "modules.publishing.publication.PublicationVersion.objects.create",
            return_value=created,
        ) as create_version,
        patch("modules.publishing.publication.record_audit_event") as record_audit,
    ):
        result = restore_publication.__wrapped__(
            source_publication_id=source.pk,
            expected_current_version=4,
            restorer=SimpleNamespace(pk=3),
            reason="Restaurar conteúdo validado anteriormente.",
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=True,
            critical_override_reason="",
        )

    assert result is created
    apply_snapshot.assert_called_once()
    validate_references.assert_called_once()
    locked.save.assert_called_once_with()
    created_fields = create_version.call_args.kwargs
    assert created_fields["revision"] is None
    assert created_fields["restored_from"] is source
    assert created_fields["version"] == 5
    assert created_fields["snapshot"] == source.snapshot
    assert created_fields["approved_by"] is source.approved_by
    assert created_fields["published_by"].pk == 3
    assert record_audit.call_args.kwargs["action"] == (AuditEvent.Action.PUBLICATION_RESTORE)
    assert record_audit.call_args.kwargs["metadata"]["source_version"] == 2


def test_restoration_model_and_endpoint_preserve_history():
    assert PublicationVersion._meta.get_field("revision").null is True
    restored_from = PublicationVersion._meta.get_field("restored_from")
    assert restored_from.remote_field.on_delete.__name__ == "PROTECT"
    assert hasattr(restore_publication, "__wrapped__")
    assert PublicationVersionRestoreView.required_admin_action == AdminAction.PUBLISH

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/admin/editorial/publications/{publication_id}/restore"][
        "post"
    ]
    assert operation["operationId"] == "restorePublicationVersion"
    assert operation["security"] == [{"cookieAuth": []}]
