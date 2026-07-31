from django.conf import settings
from django.db import models

from modules.core.models import UUIDTimeStampedModel


class AdministrativeRegionScope(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="administrative_region_scopes",
    )
    region = models.ForeignKey(
        "regions.Region",
        on_delete=models.CASCADE,
        related_name="administrative_user_scopes",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("user_id", "region_id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "region"),
                name="admin_scope_user_region_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("user", "is_active"),
                name="admin_scope_user_active_idx",
            ),
        ]
