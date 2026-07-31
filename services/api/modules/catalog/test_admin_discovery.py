from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.test import override_settings
from drf_spectacular.generators import SchemaGenerator

from modules.accounts.permissions import AdminAction
from modules.audit.models import AuditEvent

from .admin_discovery import (
    GooglePlacesPreview,
    _record_preview,
    execute_google_places_preview,
)
from .admin_views import GooglePlacesPreviewView
from .external_discovery import RecordedDiscovery
from .google_places import PlaceCandidate


def candidate() -> PlaceCandidate:
    return PlaceCandidate(
        place_id="place-123",
        display_name="Nome temporário",
        formatted_address="Endereço temporário",
        latitude=-2.56,
        longitude=-54.97,
        primary_type="restaurant",
        google_maps_uri="https://maps.google.com/?cid=123",
    )


def route():
    return SimpleNamespace(
        pk=uuid4(),
        slug="pindobal",
        region=SimpleNamespace(pk=uuid4(), slug="santarem-alter-do-chao"),
    )


def test_preview_executes_provider_before_recording_minimal_result():
    item = candidate()
    recorded = RecordedDiscovery(run_id=str(uuid4()), reference_count=1)
    current_route = route()

    with (
        patch(
            "modules.catalog.admin_discovery.search_nearby",
            return_value=[item],
        ) as search,
        patch(
            "modules.catalog.admin_discovery._record_preview",
            return_value=recorded,
        ) as record,
    ):
        preview = execute_google_places_preview(
            api_key="server-only-key",
            route=current_route,
            actor=SimpleNamespace(pk=1),
            request_id=uuid4(),
            latitude=-2.56,
            longitude=-54.97,
            radius_meters=10_000,
            included_types=["restaurant"],
            max_results=10,
        )

    assert preview.candidates == [item]
    assert preview.recorded is recorded
    assert search.call_args.kwargs["api_key"] == "server-only-key"
    assert record.call_args.kwargs["candidates"] == [item]


def test_recording_persists_only_place_ids_and_audits_without_payload():
    item = candidate()
    current_route = route()
    recorded = RecordedDiscovery(run_id=str(uuid4()), reference_count=1)

    with (
        patch(
            "modules.catalog.admin_discovery.record_google_places_discovery",
            return_value=recorded,
        ) as persist,
        patch("modules.catalog.admin_discovery.record_audit_event") as audit,
    ):
        result = _record_preview.__wrapped__(
            route=current_route,
            actor=SimpleNamespace(pk=1),
            request_id=uuid4(),
            latitude=-2.56,
            longitude=-54.97,
            radius_meters=10_000,
            included_types=["restaurant"],
            max_results=10,
            candidates=[item],
        )

    assert result is recorded
    assert persist.call_args.kwargs["place_ids"] == ["place-123"]
    assert "display_name" not in persist.call_args.kwargs
    assert audit.call_args.kwargs["action"] == AuditEvent.Action.EXTERNAL_DISCOVERY
    assert audit.call_args.kwargs["metadata"] == {
        "provider": "google_places",
        "route_id": str(current_route.pk),
        "result_count": 1,
        "radius_meters": 10_000,
        "max_results": 10,
        "type_count": 1,
    }
    assert "Nome temporário" not in str(audit.call_args.kwargs)


@override_settings(
    GOOGLE_PLACES_ADMIN_PREVIEW_ENABLED=True,
    GOOGLE_MAPS_API_KEY="server-only-key",
)
def test_preview_endpoint_is_attributed_ephemeral_and_region_scoped():
    current_route = route()
    recorded = RecordedDiscovery(run_id=str(uuid4()), reference_count=1)
    request = SimpleNamespace(
        data={
            "region_slug": current_route.region.slug,
            "route_slug": current_route.slug,
            "latitude": -2.56,
            "longitude": -54.97,
            "radius_meters": 10_000,
            "included_types": ["restaurant", "restaurant"],
            "max_results": 10,
        },
        request_id=uuid4(),
        user=SimpleNamespace(pk=1),
    )
    with (
        patch(
            "modules.catalog.admin_views.get_object_or_404",
            return_value=current_route,
        ),
        patch(
            "modules.catalog.admin_views.has_admin_action",
            return_value=True,
        ) as authorize,
        patch(
            "modules.catalog.admin_views.execute_google_places_preview",
            return_value=GooglePlacesPreview(
                recorded=recorded,
                candidates=[candidate()],
            ),
        ) as execute,
    ):
        response = GooglePlacesPreviewView().post(request)

    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store"
    assert response.data["attribution"] == "Google Maps"
    assert response.data["candidates"][0]["display_name"] == "Nome temporário"
    assert execute.call_args.kwargs["included_types"] == ["restaurant"]
    authorize.assert_called_once_with(
        request.user,
        AdminAction.DISCOVER_EXTERNAL,
        region=current_route.region,
    )


@override_settings(GOOGLE_PLACES_ADMIN_PREVIEW_ENABLED=False)
def test_preview_endpoint_stops_before_route_or_provider_when_disabled():
    request = SimpleNamespace(data={}, request_id=uuid4(), user=SimpleNamespace(pk=1))

    with patch("modules.catalog.admin_views.execute_google_places_preview") as execute:
        response = GooglePlacesPreviewView().post(request)

    assert response.status_code == 503
    assert response.data["code"] == "external_discovery_disabled"
    execute.assert_not_called()


def test_preview_endpoint_is_session_protected_throttled_and_documented():
    assert GooglePlacesPreviewView.required_admin_action == AdminAction.DISCOVER_EXTERNAL
    assert GooglePlacesPreviewView.throttle_classes[0].scope == "google_places_preview"

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/admin/discovery/google-places/preview"]["post"]
    assert operation["operationId"] == "previewGooglePlacesCandidates"
    assert operation["security"] == [{"cookieAuth": []}]
