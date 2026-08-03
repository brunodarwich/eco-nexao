"""Ensaios operacionais de backup, rollback e resposta a incidentes — Tarefa V3.

Verifica os 4 pilares de resiliência do MVP sem dependência de banco físico:
1. Backup de banco de dados e estrutura de dumps (dumpdata / loaddata).
2. Rollback de aplicação (migrações reversíveis de esquema/dados sem perda).
3. Rollback de conteúdo editorial (versões imutáveis e histórico auditável).
4. Resposta a incidentes (conflitos de concorrência e segregação de funções).

_Requisitos: RF-10, RNF-05_
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.db.migrations.loader import MigrationLoader

from modules.accounts.permissions import AdminAction
from modules.audit.models import AuditEvent
from modules.publishing.models import EditorialRevision, PublicationVersion
from modules.publishing.publication import (
    EditorialWorkflowError,
    restore_publication,
    validate_restoration_request,
)
from modules.publishing.views import PublicationVersionRestoreView

# ══════════════════════════════════════════════════════════════════════════════
# 1. Ensaios de Backup e Restauração de Banco de Dados
# ══════════════════════════════════════════════════════════════════════════════


def test_database_backup_and_restore_commands_are_registered():
    """Garante que os comandos de backup e restauração (dumpdata / loaddata) estão disponíveis."""
    from django.core.management import get_commands

    commands = get_commands()
    assert "dumpdata" in commands
    assert "loaddata" in commands


# ══════════════════════════════════════════════════════════════════════════════
# 2. Ensaios de Rollback de Aplicação (Migrations Reversíveis)
# ══════════════════════════════════════════════════════════════════════════════


def test_core_migrations_are_fully_reversible():
    """Verifica se as migrações principais possuem operações de reversão."""
    # Instancia o carregador de migrações sem conexão com banco de dados ativa
    loader = MigrationLoader(connection=None, load=False)
    loader.load_disk()

    core_apps = {"accounts", "audit", "catalog", "core", "publishing", "regions", "routes"}

    for (app_label, migration_name), migration_obj in loader.disk_migrations.items():
        if app_label in core_apps:
            assert hasattr(migration_obj, "operations"), (
                f"Migração {app_label}.{migration_name} inválida."
            )
            for op in migration_obj.operations:
                if op.__class__.__name__ == "RunPython":
                    err = f"Migration {app_label}.{migration_name} sem reverse_code."
                    assert op.reverse_code is not None, err


# ══════════════════════════════════════════════════════════════════════════════
# 3. Ensaios de Rollback de Conteúdo Editorial
# ══════════════════════════════════════════════════════════════════════════════


def test_content_rollback_service_reapplies_snapshot_and_audit():
    """Valida o serviço restore_publication recriando snapshot v1 e auditando a restauração."""
    source_v1 = SimpleNamespace(
        pk="pub-v1",
        version=1,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-123",
        region=SimpleNamespace(pk="region-1"),
        approved_by=SimpleNamespace(pk=2),
        approved_by_id=2,
        snapshot={"slug": "rota-pindobal", "public_name": "Rota Pindobal Original"},
    )
    current_v2 = SimpleNamespace(
        pk="pub-v2",
        version=2,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-123",
    )
    locked_target = MagicMock()

    source_query = MagicMock()
    source_query.get.return_value = source_v1

    current_query = MagicMock()
    current_query.filter.return_value.order_by.return_value.first.return_value = current_v2

    restored_v3 = SimpleNamespace(
        pk="pub-v3",
        version=3,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-123",
        checksum="c" * 64,
        reason="Rollback de emergência para v1 devido a inconsistência na v2",
        critical_information_current=True,
    )

    restorer = SimpleNamespace(pk=3)

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
            return_value=locked_target,
        ),
        patch("modules.publishing.publication.apply_snapshot_to_target") as apply_snapshot,
        patch("modules.publishing.publication.validate_target_references") as validate_refs,
        patch(
            "modules.publishing.publication.PublicationVersion.objects.create",
            return_value=restored_v3,
        ) as create_version,
        patch("modules.publishing.publication.record_audit_event") as record_audit,
    ):
        result = restore_publication.__wrapped__(
            source_publication_id=source_v1.pk,
            expected_current_version=2,
            restorer=restorer,
            reason="Rollback de emergência para v1 devido a inconsistência na v2",
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=True,
            critical_override_reason="",
        )

    assert result is restored_v3
    apply_snapshot.assert_called_once_with(
        locked_target,
        target_type=EditorialRevision.TargetType.ROUTE,
        snapshot={"slug": "rota-pindobal", "public_name": "Rota Pindobal Original"},
    )
    validate_refs.assert_called_once()
    locked_target.save.assert_called_once_with()

    created_args = create_version.call_args.kwargs
    assert created_args["restored_from"] is source_v1
    assert created_args["version"] == 3
    assert created_args["snapshot"] == source_v1.snapshot

    audit_args = record_audit.call_args.kwargs
    assert audit_args["action"] == AuditEvent.Action.PUBLICATION_RESTORE
    assert audit_args["metadata"]["source_version"] == 1
    assert audit_args["metadata"]["version"] == 3


def test_content_rollback_endpoint_and_models_enforce_protections():
    """Garante que PublicationVersionRestoration preserva histórico e exige permissão PUBLISH."""
    assert PublicationVersion._meta.get_field("revision").null is True
    restored_from_field = PublicationVersion._meta.get_field("restored_from")
    assert restored_from_field.remote_field.on_delete.__name__ == "PROTECT"
    assert PublicationVersionRestoreView.required_admin_action == AdminAction.PUBLISH


# ══════════════════════════════════════════════════════════════════════════════
# 4. Ensaios de Resposta a Incidentes e Resiliência
# ══════════════════════════════════════════════════════════════════════════════


def test_incident_response_blocks_stale_rollback_concurrency():
    """Incidente de Concorrência: tenta rollback informando versão desatualizada (409 Conflict)."""
    source_v1 = SimpleNamespace(
        pk="pub-v1",
        version=1,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-123",
        region=SimpleNamespace(pk="region-1"),
    )
    current_v3 = SimpleNamespace(
        pk="pub-v3",
        version=3,
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id="route-123",
    )

    source_query = MagicMock()
    source_query.get.return_value = source_v1

    current_query = MagicMock()
    current_query.filter.return_value.order_by.return_value.first.return_value = current_v3

    with (
        patch(
            "modules.publishing.publication.PublicationVersion.objects.select_related",
            return_value=source_query,
        ),
        patch(
            "modules.publishing.publication.PublicationVersion.objects.select_for_update",
            return_value=current_query,
        ),
        patch("modules.publishing.publication._locked_target_for"),
        pytest.raises(EditorialWorkflowError) as conflict,
    ):
        restore_publication.__wrapped__(
            source_publication_id=source_v1.pk,
            expected_current_version=2,  # Esperava v2, mas a versão atual é v3
            restorer=SimpleNamespace(pk=3),
            reason="Tentativa de rollback obsoleta",
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=True,
            critical_override_reason="",
        )

    assert conflict.value.code == "publication_conflict"
    assert conflict.value.status_code == 409
    assert "expected_current_version" in conflict.value.field_errors


def test_incident_response_enforces_segregation_and_reason_validation():
    """Incidente de Governança: bloqueia restauração pelo mesmo usuário que aprovou a versão."""
    source_v1 = SimpleNamespace(approved_by_id=2)

    # Motivo curto
    with pytest.raises(EditorialWorkflowError) as short_reason:
        validate_restoration_request(
            source_v1,
            restorer=SimpleNamespace(pk=3),
            reason="curto",
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=True,
            critical_override_reason="",
        )
    assert short_reason.value.code == "restoration_reason_required"

    # Segregação de funções violada
    with pytest.raises(EditorialWorkflowError) as segregation:
        validate_restoration_request(
            source_v1,
            restorer=SimpleNamespace(pk=2),  # Mesmo ID do aprovador da versão
            reason="Restauração de emergência autorizada pela equipe.",
            source_confirmed=True,
            human_confirmed=True,
            critical_information_current=True,
            critical_override_reason="",
        )
    assert segregation.value.code == "restoration_segregation_required"
    assert segregation.value.status_code == 403
