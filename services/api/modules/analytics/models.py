import uuid

from django.db import models


class RawAnalyticsEvent(models.Model):
    """
    Eventos brutos de analytics coletados com consentimento prévio.
    Retenção curta (90 dias); livre de dados pessoais e coordenadas.
    """

    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_name = models.CharField(max_length=64, db_index=True)
    schema_version = models.CharField(max_length=16, default="1.0")
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # A ingestão operacional não guarda identificadores de visitantes.
    anonymous_id = models.UUIDField(null=True, blank=True, editable=False)
    session_id = models.UUIDField(null=True, blank=True, editable=False)
    consent_id = models.UUIDField(null=True, blank=True, editable=False)
    consent_version = models.CharField(max_length=16, default="1.0")
    app_version = models.CharField(max_length=32, default="1.0.0")

    screen_name = models.CharField(max_length=64, blank=True)
    region_id = models.CharField(max_length=64, blank=True, db_index=True)
    route_id = models.CharField(max_length=64, blank=True, db_index=True)
    actor_id = models.CharField(max_length=64, blank=True)
    stage_id = models.CharField(max_length=64, blank=True)
    source = models.CharField(max_length=64, blank=True)
    campaign_id = models.CharField(max_length=64, blank=True)
    device_class = models.CharField(max_length=32, blank=True)
    network_class = models.CharField(max_length=32, blank=True)
    display_mode = models.CharField(max_length=32, blank=True)

    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Evento Bruto de Analytics"
        verbose_name_plural = "Eventos Brutos de Analytics"
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.event_name} ({self.occurred_at})"


class DailyAnalyticsAggregate(models.Model):
    """
    Métricas agregadas diárias por evento, região e rota.
    Sem possibilidade de reidentificação de usuários.
    """

    date = models.DateField(db_index=True)
    event_name = models.CharField(max_length=64, db_index=True)
    region_slug = models.CharField(max_length=64, blank=True, db_index=True)
    route_slug = models.CharField(max_length=64, blank=True, db_index=True)
    # String vazia representa dimensão não aplicável e mantém a chave agregada determinística.
    support_point_id = models.CharField(max_length=36, blank=True, default="", db_index=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Agregação Diária de Analytics"
        verbose_name_plural = "Agregações Diárias de Analytics"
        unique_together = ("date", "event_name", "region_slug", "route_slug", "support_point_id")
        ordering = ["-date", "event_name"]

    def __str__(self):
        return f"{self.date} - {self.event_name}: {self.count}"
