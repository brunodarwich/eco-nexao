from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from modules.core.models import EditorialStatus, UUIDTimeStampedModel


class Category(UUIDTimeStampedModel):
    slug = models.SlugField(max_length=120, unique=True)
    public_name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("public_name",)
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.public_name


class Actor(UUIDTimeStampedModel):
    class ActorKind(models.TextChoices):
        BUSINESS = "business", "Empresa"
        INDIVIDUAL_PROVIDER = "individual_provider", "Prestador individual"
        COMMUNITY = "community", "Comunidade"
        INSTITUTION = "institution", "Instituição"
        SUPPORT = "support", "Ponto de apoio"

    class PartnershipType(models.TextChoices):
        EDITORIAL = "editorial", "Editorial"
        PARTNER = "partner", "Parceiro"
        SPONSORED = "sponsored", "Patrocinado"

    external_id = models.CharField(max_length=160, unique=True)
    actor_kind = models.CharField(max_length=24, choices=ActorKind.choices)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="actors")
    slug = models.SlugField(max_length=140, unique=True)
    public_name = models.CharField(max_length=160)
    legal_name = models.CharField(max_length=200, blank=True)
    short_description = models.CharField(max_length=180)
    full_description = models.TextField(blank=True)
    services = models.JSONField(default=list, blank=True)
    editorial_status = models.CharField(
        max_length=16,
        choices=EditorialStatus.choices,
        default=EditorialStatus.DRAFT,
        db_index=True,
    )
    partnership_type = models.CharField(
        max_length=16,
        choices=PartnershipType.choices,
        default=PartnershipType.EDITORIAL,
    )

    class Meta:
        ordering = ("public_name",)
        indexes = [
            models.Index(
                fields=("category", "editorial_status"),
                name="actor_category_state_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.public_name


class ActorLocation(UUIDTimeStampedModel):
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE, related_name="locations")
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.PROTECT,
        related_name="actor_locations",
    )
    label = models.CharField(max_length=120)
    address_fields = models.JSONField(default=dict, blank=True)
    point = models.PointField(srid=4326, null=True, blank=True)
    service_area = models.MultiPolygonField(srid=4326, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    public_visibility = models.BooleanField(default=True)

    class Meta:
        ordering = ("actor_id", "-is_primary", "label")
        constraints = [
            models.UniqueConstraint(
                fields=("actor", "region", "label"),
                name="location_actor_region_label_uniq",
            ),
            models.UniqueConstraint(
                fields=("actor", "region"),
                condition=Q(is_primary=True),
                name="location_one_primary_per_region",
            ),
        ]
        indexes = [
            models.Index(
                fields=("region", "public_visibility"),
                name="location_region_public_idx",
            ),
        ]


class RouteActor(UUIDTimeStampedModel):
    class RouteRole(models.TextChoices):
        EXPERIENCE = "experience", "Experiência"
        SUPPORT = "support", "Apoio"
        START = "start", "Início"
        STOP = "stop", "Parada"
        EMERGENCY = "emergency", "Emergência"
        SERVICE = "service", "Serviço"

    route = models.ForeignKey(
        "routes.Route",
        on_delete=models.CASCADE,
        related_name="actor_links",
    )
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE, related_name="route_links")
    stage = models.ForeignKey(
        "routes.RouteStage",
        on_delete=models.SET_NULL,
        related_name="actor_links",
        null=True,
        blank=True,
    )
    route_role = models.CharField(max_length=16, choices=RouteRole.choices)
    editorial_position = models.PositiveSmallIntegerField(default=1)
    is_featured = models.BooleanField(default=False)
    sponsorship_label = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ("route_id", "editorial_position", "actor_id")
        constraints = [
            models.UniqueConstraint(
                fields=("route", "actor", "stage", "route_role"),
                name="route_actor_context_uniq",
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=Q(editorial_position__gt=0),
                name="route_actor_position_positive",
            ),
        ]

    def clean(self):
        super().clean()
        if self.stage_id and self.route_id and self.stage.route_id != self.route_id:
            raise ValidationError(
                {"stage": "A etapa do vínculo de catálogo deve pertencer à rota informada."}
            )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)


class ContactChannel(UUIDTimeStampedModel):
    class ChannelType(models.TextChoices):
        PHONE = "phone", "Telefone"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"
        WEBSITE = "website", "Site"
        INSTAGRAM = "instagram", "Instagram"

    actor = models.ForeignKey(Actor, on_delete=models.CASCADE, related_name="contact_channels")
    channel_type = models.CharField(max_length=16, choices=ChannelType.choices)
    value_encrypted = models.TextField(blank=True)
    public_value = models.CharField(max_length=500, blank=True)
    is_public = models.BooleanField(default=False)
    authorization_reference = models.CharField(max_length=200, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("actor", "channel_type", "public_value"),
                name="contact_public_channel_uniq",
            ),
            models.CheckConstraint(
                condition=Q(is_public=False)
                | (Q(public_value__gt="") & Q(authorization_reference__gt="")),
                name="contact_public_requires_authorization",
            ),
        ]


class OperatingHours(UUIDTimeStampedModel):
    actor_location = models.ForeignKey(
        ActorLocation,
        on_delete=models.CASCADE,
        related_name="operating_hours",
    )
    weekday = models.PositiveSmallIntegerField(null=True, blank=True)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    exception_date = models.DateField(null=True, blank=True)
    public_note = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ("actor_location_id", "exception_date", "weekday")
        constraints = [
            models.CheckConstraint(
                condition=Q(weekday__isnull=True) | Q(weekday__range=(0, 6)),
                name="hours_weekday_valid",
            ),
            models.CheckConstraint(
                condition=Q(exception_date__isnull=False) | Q(weekday__isnull=False),
                name="hours_day_or_exception",
            ),
            models.CheckConstraint(
                condition=Q(is_closed=True)
                | (Q(opens_at__isnull=False) & Q(closes_at__isnull=False)),
                name="hours_open_requires_times",
            ),
        ]


class ExternalSourceReference(UUIDTimeStampedModel):
    class Provider(models.TextChoices):
        GOOGLE_PLACES = "google_places", "Google Places"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        RESEARCHING = "researching", "Em apuração"
        LINKED = "linked", "Vinculado"
        REJECTED = "rejected", "Descartado"

    provider = models.CharField(max_length=32, choices=Provider.choices)
    provider_record_id = models.CharField(max_length=255)
    actor = models.ForeignKey(
        Actor,
        on_delete=models.SET_NULL,
        related_name="external_source_references",
        null=True,
        blank=True,
    )
    review_status = models.CharField(
        max_length=16,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        db_index=True,
    )
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-last_seen_at", "provider_record_id")
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "provider_record_id"),
                name="external_source_provider_id_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("provider", "last_seen_at"),
                name="external_source_seen_idx",
            ),
        ]


class ExternalDiscoveryRun(UUIDTimeStampedModel):
    provider = models.CharField(
        max_length=32,
        choices=ExternalSourceReference.Provider.choices,
    )
    context_key = models.SlugField(max_length=160)
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_meters = models.PositiveIntegerField()
    included_types = models.JSONField(default=list)
    max_results = models.PositiveSmallIntegerField()
    result_count = models.PositiveSmallIntegerField()
    executed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-executed_at",)
        indexes = [
            models.Index(
                fields=("provider", "context_key", "executed_at"),
                name="external_run_context_idx",
            ),
        ]


class ExternalDiscoveryHit(UUIDTimeStampedModel):
    run = models.ForeignKey(
        ExternalDiscoveryRun,
        on_delete=models.CASCADE,
        related_name="hits",
    )
    reference = models.ForeignKey(
        ExternalSourceReference,
        on_delete=models.CASCADE,
        related_name="discovery_hits",
    )
    result_position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ("run_id", "result_position")
        constraints = [
            models.UniqueConstraint(
                fields=("run", "reference"),
                name="external_hit_run_reference_uniq",
            ),
            models.UniqueConstraint(
                fields=("run", "result_position"),
                name="external_hit_run_position_uniq",
            ),
            models.CheckConstraint(
                condition=Q(result_position__gt=0),
                name="external_hit_position_positive",
            ),
        ]
