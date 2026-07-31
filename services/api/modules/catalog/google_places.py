import json
from collections.abc import Callable
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"
FIELD_MASK = ",".join(
    (
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.primaryType",
        "places.googleMapsUri",
    )
)


class GooglePlacesError(Exception):
    """Erro operacional seguro ao consultar a Places API."""


@dataclass(frozen=True)
class PlaceCandidate:
    place_id: str
    display_name: str
    formatted_address: str
    latitude: float | None
    longitude: float | None
    primary_type: str
    google_maps_uri: str


Transport = Callable[[Request, float], bytes]


def _default_transport(request: Request, timeout: float) -> bytes:
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read()


def search_nearby(
    *,
    api_key: str,
    latitude: float,
    longitude: float,
    radius_meters: float,
    included_types: list[str],
    max_results: int,
    timeout_seconds: float = 15,
    transport: Transport = _default_transport,
) -> list[PlaceCandidate]:
    key = api_key.strip()
    if not key:
        raise GooglePlacesError("A credencial do Google Maps não foi configurada.")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise GooglePlacesError("As coordenadas informadas são inválidas.")
    if not 1 <= radius_meters <= 50_000:
        raise GooglePlacesError("O raio deve estar entre 1 e 50.000 metros.")
    if not 1 <= max_results <= 20:
        raise GooglePlacesError("O limite deve estar entre 1 e 20 resultados.")

    types = list(dict.fromkeys(item.strip() for item in included_types if item.strip()))
    if not types or len(types) > 50:
        raise GooglePlacesError("Informe entre 1 e 50 tipos de lugar.")

    payload = {
        "includedTypes": types,
        "maxResultCount": max_results,
        "languageCode": "pt-BR",
        "rankPreference": "POPULARITY",
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_meters,
            }
        },
    }
    request = Request(
        NEARBY_SEARCH_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
        method="POST",
    )

    try:
        raw_response = transport(request, timeout_seconds)
        response = json.loads(raw_response)
    except HTTPError as error:
        if error.code == 403:
            reason = _safe_google_error_reason(error)
            reason_suffix = f" Motivo informado pelo Google: {reason}." if reason else ""
            raise GooglePlacesError(
                "A Places API recusou a consulta (HTTP 403). Confirme a ativação da "
                "Places API (New), o faturamento e as restrições server-side da chave."
                f"{reason_suffix}"
            ) from None
        if error.code == 429:
            raise GooglePlacesError(
                "A cota da Places API foi atingida (HTTP 429). Revise limites e orçamento."
            ) from None
        raise GooglePlacesError(f"A Places API recusou a consulta (HTTP {error.code}).") from None
    except URLError:
        raise GooglePlacesError("Não foi possível conectar à Places API.") from None
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        raise GooglePlacesError("A Places API retornou uma resposta inválida.") from None

    places = response.get("places", []) if isinstance(response, dict) else []
    if not isinstance(places, list):
        raise GooglePlacesError("A Places API retornou uma resposta inválida.")

    candidates: list[PlaceCandidate] = []
    for place in places:
        if not isinstance(place, dict) or not isinstance(place.get("id"), str):
            continue
        display_name = place.get("displayName", {})
        location = place.get("location", {})
        candidates.append(
            PlaceCandidate(
                place_id=place["id"],
                display_name=(
                    display_name.get("text", "") if isinstance(display_name, dict) else ""
                ),
                formatted_address=str(place.get("formattedAddress", "")),
                latitude=_optional_number(location, "latitude"),
                longitude=_optional_number(location, "longitude"),
                primary_type=str(place.get("primaryType", "")),
                google_maps_uri=str(place.get("googleMapsUri", "")),
            )
        )
    return candidates


def _optional_number(value: object, key: str) -> float | None:
    if not isinstance(value, dict):
        return None
    number = value.get(key)
    return float(number) if isinstance(number, int | float) else None


def _safe_google_error_reason(error: HTTPError) -> str:
    try:
        payload = json.loads(error.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return ""
    if not isinstance(payload, dict):
        return ""
    details = payload.get("error", {}).get("details", [])
    if not isinstance(details, list):
        return ""
    for detail in details:
        if not isinstance(detail, dict):
            continue
        reason = detail.get("reason")
        if isinstance(reason, str) and reason:
            return reason
        violations = detail.get("violations", [])
        if not isinstance(violations, list):
            continue
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            reason = violation.get("reason")
            if isinstance(reason, str) and reason:
                return reason
    return ""
