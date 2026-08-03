from django.db import models

from modules.core.models import UUIDTimeStampedModel


class PublicReport(UUIDTimeStampedModel):
    class ReportType(models.TextChoices):
        INCORRECT_INFO = "incorrect_info", "Informação Incorreta"
        CLOSED_LOCATION = "closed_location", "Local Fechado ou Inacessível"
        WRONG_CONTACT = "wrong_contact", "Contato Desatualizado"
        SAFETY_WARNING = "safety_warning", "Alerta de Segurança"
        OTHER = "other", "Outro Assunto"

    class TargetType(models.TextChoices):
        ROUTE = "route", "Rota"
        ACTOR = "actor", "Ator / Ponto Local"
        GENERAL = "general", "Geral"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        REVIEWED = "reviewed", "Revisado"
        REJECTED = "rejected", "Rejeitado"
        ACTIONED = "actioned", "Ação Concluída"

    report_type = models.CharField(
        max_length=32,
        choices=ReportType.choices,
        default=ReportType.INCORRECT_INFO,
    )
    target_type = models.CharField(
        max_length=32,
        choices=TargetType.choices,
        default=TargetType.GENERAL,
    )
    target_id = models.UUIDField(null=True, blank=True)
    target_slug = models.CharField(max_length=120, blank=True, default="")
    region_slug = models.CharField(max_length=120, blank=True, default="")
    description = models.TextField(max_length=1000)
    reporter_contact = models.CharField(max_length=120, blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    moderation_note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Relato Público"
        verbose_name_plural = "Relatos Públicos"

    def __str__(self):
        return f"Relato {self.report_type} ({self.get_status_display()})"
