from dataclasses import dataclass
from decimal import Decimal

from django.core.validators import validate_slug
from django.db import transaction
from django.utils import timezone

from modules.catalog.models import (
    ExternalDiscoveryHit,
    ExternalDiscoveryRun,
    ExternalSourceReference,
)


@dataclass(frozen=True)
class RecordedDiscovery:
    run_id: str
    reference_count: int


def normalize_place_ids(place_ids: list[str]) -> list[str]:
    return list(dict.fromkeys(place_id.strip() for place_id in place_ids if place_id.strip()))


@transaction.atomic
def record_google_places_discovery(
    *,
    context_key: str,
    latitude: float,
    longitude: float,
    radius_meters: float,
    included_types: list[str],
    max_results: int,
    place_ids: list[str],
) -> RecordedDiscovery:
    validate_slug(context_key)
    normalized_ids = normalize_place_ids(place_ids)
    now = timezone.now()
    run = ExternalDiscoveryRun.objects.create(
        provider=ExternalSourceReference.Provider.GOOGLE_PLACES,
        context_key=context_key,
        center_latitude=Decimal(str(latitude)),
        center_longitude=Decimal(str(longitude)),
        radius_meters=round(radius_meters),
        included_types=list(dict.fromkeys(item.strip() for item in included_types if item.strip())),
        max_results=max_results,
        result_count=len(normalized_ids),
        executed_at=now,
    )

    for position, place_id in enumerate(normalized_ids, start=1):
        reference, created = ExternalSourceReference.objects.get_or_create(
            provider=ExternalSourceReference.Provider.GOOGLE_PLACES,
            provider_record_id=place_id,
            defaults={"first_seen_at": now, "last_seen_at": now},
        )
        if not created:
            ExternalSourceReference.objects.filter(pk=reference.pk).update(
                last_seen_at=now,
                updated_at=now,
            )
        ExternalDiscoveryHit.objects.create(
            run=run,
            reference=reference,
            result_position=position,
        )

    return RecordedDiscovery(run_id=str(run.id), reference_count=len(normalized_ids))
