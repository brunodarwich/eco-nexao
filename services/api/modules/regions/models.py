from django.contrib.gis.db import models

from modules.core.models import EditorialStatus, UUIDTimeStampedModel


class Region(UUIDTimeStampedModel):
    slug = models.SlugField(max_length=120, unique=True)
    public_name = models.CharField(max_length=160)
    short_description = models.CharField(max_length=300, blank=True)
    boundary = models.MultiPolygonField(srid=4326, null=True, blank=True)
    center_point = models.PointField(srid=4326)
    timezone = models.CharField(max_length=64, default="America/Fortaleza")
    status = models.CharField(
        max_length=16,
        choices=EditorialStatus.choices,
        default=EditorialStatus.DRAFT,
        db_index=True,
    )
    published_version = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("public_name",)
        indexes = [
            models.Index(fields=("status", "public_name"), name="region_status_name_idx"),
        ]

    def __str__(self) -> str:
        return self.public_name
