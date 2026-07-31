from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import F, Q

from modules.core.models import EditorialStatus, UUIDTimeStampedModel


class Route(UUIDTimeStampedModel):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Fácil"
        MODERATE = "moderate", "Moderada"
        HARD = "hard", "Difícil"

    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="routes",
    )
    slug = models.SlugField(max_length=120)
    public_name = models.CharField(max_length=160)
    short_promise = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField()
    difficulty = models.CharField(max_length=16, choices=Difficulty.choices)
    estimated_cost_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_cost_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    transport_modes = models.JSONField(default=list, blank=True)
    preparation_content = models.TextField(blank=True)
    accessibility_content = models.TextField(blank=True)
    offline_enabled = models.BooleanField(default=False)
    editorial_status = models.CharField(
        max_length=16,
        choices=EditorialStatus.choices,
        default=EditorialStatus.DRAFT,
        db_index=True,
    )

    class Meta:
        ordering = ("region_id", "public_name")
        constraints = [
            models.UniqueConstraint(fields=("region", "slug"), name="route_region_slug_uniq"),
            models.CheckConstraint(
                condition=Q(duration_minutes__gt=0),
                name="route_duration_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(estimated_cost_min__isnull=True)
                    | Q(estimated_cost_max__isnull=True)
                    | Q(estimated_cost_max__gte=F("estimated_cost_min"))
                ),
                name="route_cost_range_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=("region", "editorial_status"),
                name="route_region_status_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.public_name


class RouteStage(UUIDTimeStampedModel):
    class StageType(models.TextChoices):
        START = "start", "Início"
        STOP = "stop", "Parada"
        EXPERIENCE = "experience", "Experiência"
        SUPPORT = "support", "Apoio"
        END = "end", "Fim"

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="stages")
    position = models.PositiveSmallIntegerField()
    public_name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    point = models.PointField(srid=4326)
    arrival_guidance = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    stage_type = models.CharField(max_length=16, choices=StageType.choices)
    is_optional = models.BooleanField(default=False)

    class Meta:
        ordering = ("route_id", "position")
        constraints = [
            models.UniqueConstraint(fields=("route", "position"), name="stage_route_position_uniq"),
            models.CheckConstraint(condition=Q(position__gt=0), name="stage_position_positive"),
            models.CheckConstraint(
                condition=Q(duration_minutes__isnull=True) | Q(duration_minutes__gt=0),
                name="stage_duration_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.route}: {self.position}. {self.public_name}"


class RouteSegment(UUIDTimeStampedModel):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="segments")
    from_stage = models.ForeignKey(
        RouteStage,
        on_delete=models.PROTECT,
        related_name="outgoing_segments",
    )
    to_stage = models.ForeignKey(
        RouteStage,
        on_delete=models.PROTECT,
        related_name="incoming_segments",
    )
    geometry = models.LineStringField(srid=4326)
    transport_mode = models.CharField(max_length=32)
    distance_meters = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField()
    instructions = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("route", "from_stage", "to_stage"),
                name="segment_path_uniq",
            ),
            models.CheckConstraint(
                condition=~Q(from_stage=F("to_stage")),
                name="segment_distinct_stages",
            ),
            models.CheckConstraint(
                condition=Q(distance_meters__gt=0),
                name="segment_distance_positive",
            ),
            models.CheckConstraint(
                condition=Q(duration_minutes__gt=0),
                name="segment_duration_positive",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.route_id and self.from_stage_id and self.from_stage.route_id != self.route_id:
            errors["from_stage"] = "A etapa inicial deve pertencer à mesma rota do segmento."
        if self.route_id and self.to_stage_id and self.to_stage.route_id != self.route_id:
            errors["to_stage"] = "A etapa final deve pertencer à mesma rota do segmento."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)


class Alert(UUIDTimeStampedModel):
    class Severity(models.TextChoices):
        INFO = "info", "Informativo"
        WARNING = "warning", "Atenção"
        CRITICAL = "critical", "Crítico"

    region = models.ForeignKey("regions.Region", on_delete=models.CASCADE, related_name="alerts")
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="alerts",
        null=True,
        blank=True,
    )
    stage = models.ForeignKey(
        RouteStage,
        on_delete=models.CASCADE,
        related_name="alerts",
        null=True,
        blank=True,
    )
    severity = models.CharField(max_length=16, choices=Severity.choices)
    title = models.CharField(max_length=160)
    description = models.TextField()
    alternative = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=EditorialStatus.choices,
        default=EditorialStatus.DRAFT,
        db_index=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__isnull=True) | Q(ends_at__gt=F("starts_at")),
                name="alert_period_valid",
            ),
            models.CheckConstraint(
                condition=Q(stage__isnull=True) | Q(route__isnull=False),
                name="alert_stage_requires_route",
            ),
        ]
        indexes = [
            models.Index(
                fields=("region", "status", "severity"),
                name="alert_region_state_idx",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.route_id and self.region_id and self.route.region_id != self.region_id:
            errors["route"] = "A rota do alerta deve pertencer à região informada."
        if self.stage_id and not self.route_id:
            errors["stage"] = "Um alerta de etapa também deve informar a rota."
        elif self.stage_id and self.stage.route_id != self.route_id:
            errors["stage"] = "A etapa do alerta deve pertencer à rota informada."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
