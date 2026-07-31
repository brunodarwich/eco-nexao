import json
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch
from urllib.error import HTTPError

import pytest
from django.core.management import call_command

from modules.catalog.external_discovery import RecordedDiscovery, normalize_place_ids
from modules.catalog.google_places import (
    FIELD_MASK,
    GooglePlacesError,
    PlaceCandidate,
    search_nearby,
)
from modules.catalog.models import (
    ExternalDiscoveryHit,
    ExternalDiscoveryRun,
    ExternalSourceReference,
)


def test_search_nearby_builds_minimal_request_and_parses_candidates() -> None:
    captured: dict[str, object] = {}

    def transport(request, timeout: float) -> bytes:
        captured["request"] = request
        captured["timeout"] = timeout
        return json.dumps(
            {
                "places": [
                    {
                        "id": "place-123",
                        "displayName": {"text": "Pousada exemplo"},
                        "formattedAddress": "Pindobal, Belterra - PA",
                        "location": {"latitude": -2.56, "longitude": -54.97},
                        "primaryType": "guest_house",
                        "googleMapsUri": "https://maps.google.com/?cid=123",
                    }
                ]
            }
        ).encode()

    candidates = search_nearby(
        api_key="test-key",
        latitude=-2.56,
        longitude=-54.97,
        radius_meters=10_000,
        included_types=["restaurant", "guest_house", "restaurant"],
        max_results=10,
        transport=transport,
    )

    request = captured["request"]
    assert request.full_url.endswith("/v1/places:searchNearby")
    assert request.headers["X-goog-api-key"] == "test-key"
    assert request.headers["X-goog-fieldmask"] == FIELD_MASK
    assert captured["timeout"] == 15
    assert json.loads(request.data)["includedTypes"] == ["restaurant", "guest_house"]
    assert candidates[0].place_id == "place-123"
    assert candidates[0].display_name == "Pousada exemplo"
    assert candidates[0].latitude == -2.56


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("api_key", "", "credencial"),
        ("radius_meters", 0, "raio"),
        ("max_results", 21, "limite"),
        ("included_types", [], "tipos"),
    ),
)
def test_search_nearby_validates_before_network(field: str, value: object, message: str) -> None:
    arguments: dict[str, object] = {
        "api_key": "test-key",
        "latitude": -2.56,
        "longitude": -54.97,
        "radius_meters": 10_000,
        "included_types": ["restaurant"],
        "max_results": 10,
        "transport": lambda *_: pytest.fail("network should not be called"),
    }
    arguments[field] = value

    with pytest.raises(GooglePlacesError, match=message):
        search_nearby(**arguments)


def test_search_nearby_does_not_expose_response_or_key_on_http_error() -> None:
    secret = "secret-google-key"

    def transport(*_args) -> bytes:
        raise HTTPError(
            url="https://places.googleapis.com",
            code=403,
            msg=f"rejected {secret}",
            hdrs=None,
            fp=None,
        )

    with pytest.raises(GooglePlacesError) as captured:
        search_nearby(
            api_key=secret,
            latitude=-2.56,
            longitude=-54.97,
            radius_meters=10_000,
            included_types=["restaurant"],
            max_results=10,
            transport=transport,
        )

    assert secret not in str(captured.value)
    assert "rejected" not in str(captured.value)
    assert "Places API (New)" in str(captured.value)


def test_search_nearby_includes_safe_google_error_reason_on_403() -> None:
    def transport(*_args) -> bytes:
        payload = {
            "error": {
                "message": "Request denied with sensitive context",
                "details": [
                    {
                        "violations": [
                            {
                                "type": "API_KEY_SERVICE_BLOCKED",
                                "subject": "apikey:secret-google-key",
                                "description": "sensitive context",
                                "reason": "API_KEY_SERVICE_BLOCKED",
                            }
                        ]
                    }
                ],
            }
        }
        raise HTTPError(
            url="https://places.googleapis.com",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=BytesIO(json.dumps(payload).encode()),
        )

    with pytest.raises(GooglePlacesError) as captured:
        search_nearby(
            api_key="secret-google-key",
            latitude=-2.56,
            longitude=-54.97,
            radius_meters=10_000,
            included_types=["restaurant"],
            max_results=10,
            transport=transport,
        )

    message = str(captured.value)
    assert "API_KEY_SERVICE_BLOCKED" in message
    assert "secret-google-key" not in message
    assert "sensitive context" not in message


def test_search_nearby_reads_safe_google_rpc_error_info_reason_on_403() -> None:
    def transport(*_args) -> bytes:
        payload = {
            "error": {
                "message": "Request blocked with sensitive context",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                        "reason": "API_KEY_HTTP_REFERRER_BLOCKED",
                        "domain": "googleapis.com",
                        "metadata": {"consumer": "secret-google-key"},
                    }
                ],
            }
        }
        raise HTTPError(
            url="https://places.googleapis.com",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=BytesIO(json.dumps(payload).encode()),
        )

    with pytest.raises(GooglePlacesError) as captured:
        search_nearby(
            api_key="secret-google-key",
            latitude=-2.56,
            longitude=-54.97,
            radius_meters=10_000,
            included_types=["restaurant"],
            max_results=10,
            transport=transport,
        )

    message = str(captured.value)
    assert "API_KEY_HTTP_REFERRER_BLOCKED" in message
    assert "secret-google-key" not in message
    assert "sensitive context" not in message


def test_normalize_place_ids_is_idempotent_and_ignores_blanks() -> None:
    assert normalize_place_ids([" place-1 ", "", "place-2", "place-1"]) == [
        "place-1",
        "place-2",
    ]


def test_persistent_models_do_not_contain_google_preview_fields() -> None:
    reference_fields = {field.name for field in ExternalSourceReference._meta.get_fields()}
    assert {
        "display_name",
        "formatted_address",
        "google_maps_uri",
        "latitude",
        "longitude",
    }.isdisjoint(reference_fields)
    assert {
        "external_source_provider_id_uniq",
    } == {constraint.name for constraint in ExternalSourceReference._meta.constraints}
    assert len(ExternalDiscoveryRun._meta.indexes) == 1
    assert len(ExternalDiscoveryHit._meta.constraints) == 3


def test_command_records_only_place_ids_and_keeps_preview_ephemeral(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-key")
    candidate = PlaceCandidate(
        place_id="place-123",
        display_name="Nome recebido do Google",
        formatted_address="Endereço recebido do Google",
        latitude=-2.56,
        longitude=-54.97,
        primary_type="restaurant",
        google_maps_uri="https://maps.google.com/?cid=123",
    )
    output = StringIO()

    with (
        patch(
            "modules.catalog.management.commands.search_google_places_pindobal.search_nearby",
            return_value=[candidate],
        ),
        patch(
            "modules.catalog.management.commands.search_google_places_pindobal."
            "record_google_places_discovery",
            return_value=RecordedDiscovery(run_id="run-123", reference_count=1),
        ) as record,
    ):
        call_command("search_google_places_pindobal", stdout=output)

    assert record.call_args.kwargs["place_ids"] == ["place-123"]
    assert "display_name" not in record.call_args.kwargs
    assert "Nome recebido do Google" in output.getvalue()
    assert "campos abaixo" in output.getvalue()


def test_command_sanitizes_preview_for_cp1252_console_without_changing_place_ids(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-key")
    candidate = PlaceCandidate(
        place_id="place-emoji-\U0001f30a",
        display_name="Praia \U0001f30a",
        formatted_address="Endereço \U0001f30a",
        latitude=-2.56,
        longitude=-54.97,
        primary_type="tourist_attraction",
        google_maps_uri="https://maps.google.com/?q=\U0001f30a",
    )
    output_bytes = BytesIO()
    output = TextIOWrapper(output_bytes, encoding="cp1252", errors="strict")

    with (
        patch(
            "modules.catalog.management.commands.search_google_places_pindobal.search_nearby",
            return_value=[candidate],
        ),
        patch(
            "modules.catalog.management.commands.search_google_places_pindobal."
            "record_google_places_discovery",
            return_value=RecordedDiscovery(run_id="run-123", reference_count=1),
        ) as record,
    ):
        call_command("search_google_places_pindobal", stdout=output)

    output.flush()
    preview = output_bytes.getvalue().decode("cp1252")
    assert "Praia ?" in preview
    assert "Place ID: place-emoji-?" in preview
    assert record.call_args.kwargs["place_ids"] == ["place-emoji-\U0001f30a"]
