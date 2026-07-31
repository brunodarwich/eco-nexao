from django.conf import settings
from django.db import models
from django.db.models import Q

from modules.core.models import UUIDTimeStampedModel


class EditorialRevision(UUIDTimeStampedModel):
    class TargetType(models.TextChoices):
        REGION = "region", "Região"
        ROUTE = "route", "Rota"
        ACTOR = "actor", "Ator"

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        REVIEW = "review", "Em revisão"
        APPROVED = "approved", "Aprovado"
        PUBLISHED = "published", "Publicado"

    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="editorial_revisions",
    )
    target_type = models.CharField(max_length=16, choices=TargetType.choices)
    target_id = models.UUIDField()
    sequence = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    base_snapshot = models.JSONField(default=dict)
    snapshot = models.JSONField(default=dict)
    diff = models.JSONField(default=list)
    lock_version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_editorial_revisions",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_editorial_revisions",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_editorial_revisions",
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_editorial_revisions",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    return_reason = models.TextField(blank=True)

    class Meta:
        ordering = ("target_type", "target_id", "-sequence")
        constraints = [
            models.UniqueConstraint(
                fields=("target_type", "target_id", "sequence"),
                name="revision_target_sequence_uniq",
            ),
            models.CheckConstraint(
                condition=Q(sequence__gt=0),
                name="revision_sequence_positive",
            ),
            models.CheckConstraint(
                condition=Q(lock_version__gt=0),
                name="revision_lock_version_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=("region", "status"),
                name="revision_region_status_idx",
            ),
            models.Index(
                fields=("target_type", "target_id", "status"),
                name="revision_target_status_idx",
            ),
        ]


class PublicationVersion(UUIDTimeStampedModel):
    revision = models.OneToOneField(
        EditorialRevision,
        on_delete=models.PROTECT,
        related_name="publication",
        null=True,
        blank=True,
    )
    restored_from = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="restorations",
        null=True,
        blank=True,
    )
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="publication_versions",
    )
    target_type = models.CharField(max_length=16, choices=EditorialRevision.TargetType.choices)
    target_id = models.UUIDField()
    version = models.PositiveIntegerField()
    snapshot = models.JSONField()
    checksum = models.CharField(max_length=64, db_index=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_publication_versions",
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="published_publication_versions",
    )
    reason = models.TextField(blank=True)
    source_confirmed = models.BooleanField()
    human_confirmed = models.BooleanField()
    critical_information_current = models.BooleanField()
    critical_override_reason = models.TextField(blank=True)
    published_at = models.DateTimeField()

    class Meta:
        ordering = ("target_type", "target_id", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=("target_type", "target_id", "version"),
                name="publication_target_version_uniq",
            ),
            models.CheckConstraint(
                condition=Q(version__gt=0),
                name="publication_version_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=("region", "published_at"),
                name="publication_region_date_idx",
            ),
            models.Index(
                fields=("target_type", "target_id", "published_at"),
                name="publication_target_date_idx",
            ),
        ]
