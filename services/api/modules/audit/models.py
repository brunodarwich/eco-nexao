import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ImmutableAuditEventQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError("Eventos de auditoria são imutáveis.")

    def delete(self):
        raise TypeError("Eventos de auditoria não podem ser removidos.")


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        AUTH_LOGIN = "auth.login", "Login administrativo"
        AUTH_LOGOUT = "auth.logout", "Logout administrativo"
        EDITORIAL_APPROVE = "editorial.approve", "Aprovação editorial"
        PUBLICATION_PUBLISH = "publication.publish", "Publicação"
        PUBLICATION_RESTORE = "publication.restore", "Restauração"
        EXTERNAL_DISCOVERY = "external.discovery", "Descoberta externa"
        IMPORT_COMMIT = "import.commit", "Confirmação de importação"
        REPORT_MODERATE = "report.moderate", "Moderação de relato"
        SUPPORT_POINT_CREATE = "catalog.support_point.create", "Cadastro de ponto de apoio"

    class Result(models.TextChoices):
        SUCCESS = "success", "Sucesso"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="administrative_audit_events",
    )
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="administrative_audit_events",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=64, choices=Action.choices, db_index=True)
    target_type = models.CharField(max_length=64)
    target_id = models.CharField(max_length=128)
    request_id = models.UUIDField(db_index=True)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    result = models.CharField(
        max_length=16,
        choices=Result.choices,
        default=Result.SUCCESS,
    )
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = ImmutableAuditEventQuerySet.as_manager()

    class Meta:
        ordering = ("-occurred_at", "-id")
        indexes = [
            models.Index(
                fields=("actor", "occurred_at"),
                name="audit_actor_date_idx",
            ),
            models.Index(
                fields=("region", "occurred_at"),
                name="audit_region_date_idx",
            ),
            models.Index(
                fields=("action", "occurred_at"),
                name="audit_action_date_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.action}:{self.target_type}:{self.target_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Eventos de auditoria são imutáveis.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Eventos de auditoria não podem ser removidos.")
