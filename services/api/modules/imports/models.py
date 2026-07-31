import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from modules.core.models import UUIDTimeStampedModel


class CatalogImportBatch(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        COMMITTED = "committed", "Confirmado"

    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    sha256 = models.CharField(max_length=64, unique=True)
    original_filename = models.CharField(max_length=255)
    byte_size = models.PositiveBigIntegerField()
    row_count = models.PositiveIntegerField()
    warning_count = models.PositiveIntegerField(default=0)
    create_count = models.PositiveIntegerField(default=0)
    update_count = models.PositiveIntegerField(default=0)
    archive_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.COMMITTED,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="catalog_import_batches",
    )
    committed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-committed_at", "-id")
        indexes = [
            models.Index(
                fields=("created_by", "committed_at"),
                name="import_batch_author_date_idx",
            ),
        ]


class CatalogImportDraft(UUIDTimeStampedModel):
    class Operation(models.TextChoices):
        CREATE = "create", "Criar"
        UPDATE = "update", "Atualizar"
        ARCHIVE = "archive", "Arquivar"

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"

    batch = models.ForeignKey(
        CatalogImportBatch,
        on_delete=models.PROTECT,
        related_name="drafts",
    )
    line_number = models.PositiveIntegerField()
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="catalog_import_drafts",
    )
    external_id = models.CharField(max_length=160)
    operation = models.CharField(max_length=16, choices=Operation.choices)
    target_actor = models.ForeignKey(
        "catalog.Actor",
        on_delete=models.PROTECT,
        related_name="catalog_import_drafts",
        null=True,
        blank=True,
    )
    payload = models.JSONField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    class Meta:
        ordering = ("batch_id", "line_number")
        constraints = [
            models.UniqueConstraint(
                fields=("batch", "line_number"),
                name="import_draft_batch_line_uniq",
            ),
            models.UniqueConstraint(
                fields=("batch", "external_id"),
                name="import_draft_batch_external_uniq",
            ),
            models.CheckConstraint(
                condition=Q(line_number__gte=2),
                name="import_draft_line_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=("region", "status"),
                name="import_draft_region_state_idx",
            ),
            models.Index(
                fields=("target_actor", "status"),
                name="import_draft_actor_state_idx",
            ),
        ]
