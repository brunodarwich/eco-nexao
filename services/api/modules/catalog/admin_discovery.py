from dataclasses import dataclass
from typing import Any

from django.db import transaction

from modules.audit.models import AuditEvent
from modules.audit.service import record_audit_event
from modules.routes.models import Route

from .external_discovery import RecordedDiscovery, record_google_places_discovery
from .google_places import PlaceCandidate, search_nearby


@dataclass(frozen=True)
class GooglePlacesPreview:
    recorded: RecordedDiscovery
    candidates: list[PlaceCandidate]


@transaction.atomic
def _record_preview(
    *,
    route: Route,
    actor: Any,
    request_id: Any,
    latitude: float,
    longitude: float,
    radius_meters: int,
    included_types: list[str],
    max_results: int,
    candidates: list[PlaceCandidate],
) -> RecordedDiscovery:
    recorded = record_google_places_discovery(
        context_key=f"route-{route.pk}",
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        included_types=included_types,
        max_results=max_results,
        place_ids=[candidate.place_id for candidate in candidates],
    )
    record_audit_event(
        actor=actor,
        region=route.region,
        action=AuditEvent.Action.EXTERNAL_DISCOVERY,
        target_type="external_discovery_run",
        target_id=recorded.run_id,
        request_id=request_id,
        metadata={
            "provider": "google_places",
            "route_id": str(route.pk),
            "result_count": recorded.reference_count,
            "radius_meters": radius_meters,
            "max_results": max_results,
            "type_count": len(included_types),
        },
    )
    return recorded


def execute_google_places_preview(
    *,
    api_key: str,
    route: Route,
    actor: Any,
    request_id: Any,
    latitude: float,
    longitude: float,
    radius_meters: int,
    included_types: list[str],
    max_results: int,
) -> GooglePlacesPreview:
    candidates = search_nearby(
        api_key=api_key,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        included_types=included_types,
        max_results=max_results,
    )
    recorded = _record_preview(
        route=route,
        actor=actor,
        request_id=request_id,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        included_types=included_types,
        max_results=max_results,
        candidates=candidates,
    )
    return GooglePlacesPreview(recorded=recorded, candidates=candidates)
