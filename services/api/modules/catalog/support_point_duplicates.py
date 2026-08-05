from dataclasses import dataclass
from difflib import SequenceMatcher

from django.contrib.gis.measure import D

from .models import ActorLocation, ContactChannel
from .support_point_normalization import (
    normalized_address,
    normalized_contact,
    normalized_name,
)

NAME_SIMILARITY_THRESHOLD = 0.85
NAME_DISTANCE_METERS = 100


@dataclass(frozen=True)
class DuplicateCandidate:
    actor_id: str
    signals: tuple[str, ...]


class DuplicateSupportPointError(Exception):
    def __init__(self, candidates: tuple[DuplicateCandidate, ...]):
        super().__init__("Foi encontrada possível duplicidade no escopo regional.")
        self.candidates = candidates
        self.candidate_ids = tuple(candidate.actor_id for candidate in candidates)


def find_support_point_duplicates(
    *,
    region,
    public_name: str,
    address_fields: dict[str, object],
    point,
    contacts: list[dict[str, object]],
) -> tuple[DuplicateCandidate, ...]:
    signals: dict[str, set[str]] = {}

    normalized_contacts = {
        normalized_contact(str(contact["channel_type"]), str(contact["value"]))
        for contact in contacts
        if contact.get("is_public")
    }
    if normalized_contacts:
        existing_contacts = ContactChannel.objects.filter(
            actor__locations__region=region,
            is_public=True,
        ).only("actor_id", "channel_type", "public_value")
        for contact in existing_contacts:
            try:
                existing_value = normalized_contact(contact.channel_type, contact.public_value)
            except ValueError:
                continue
            if existing_value in normalized_contacts:
                signals.setdefault(str(contact.actor_id), set()).add("contact_exact")

    expected_address = normalized_address(address_fields)
    regional_locations = ActorLocation.objects.filter(region=region).select_related("actor")
    for location in regional_locations.only("actor_id", "address_fields"):
        if not isinstance(location.address_fields, dict):
            continue
        if normalized_address(location.address_fields) == expected_address:
            signals.setdefault(str(location.actor_id), set()).add("address_exact")

    expected_name = normalized_name(public_name)
    nearby_locations = (
        ActorLocation.objects.filter(
            region=region,
            point__isnull=False,
            point__distance_lte=(point, D(m=NAME_DISTANCE_METERS)),
        )
        .select_related("actor")
        .only("actor_id", "actor__public_name")
    )
    for location in nearby_locations:
        similarity = SequenceMatcher(
            None,
            expected_name,
            normalized_name(location.actor.public_name),
        ).ratio()
        if similarity >= NAME_SIMILARITY_THRESHOLD:
            signals.setdefault(str(location.actor_id), set()).add("name_nearby")

    return tuple(
        DuplicateCandidate(actor_id=actor_id, signals=tuple(sorted(candidate_signals)))
        for actor_id, candidate_signals in sorted(signals.items())
    )


def reject_support_point_duplicates(**kwargs) -> None:
    candidates = find_support_point_duplicates(**kwargs)
    if candidates:
        raise DuplicateSupportPointError(candidates)
