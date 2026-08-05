import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from modules.audit.models import AuditEvent
from modules.audit.service import record_audit_event
from modules.core.models import EditorialStatus

from .models import (
    Actor,
    ActorLocation,
    ContactChannel,
    RouteActor,
    SupportPointIdempotencyRecord,
)
from .support_point_duplicates import reject_support_point_duplicates
from .support_point_relations import resolve_support_point_relations

IDEMPOTENCY_TTL = timedelta(hours=24)


class SupportPointCreationConflict(Exception):
    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SupportPointCreationResult:
    payload: dict[str, object]
    replayed: bool


def _json_default(value):
    return str(value)


def request_fingerprint(data: dict[str, object]) -> str:
    canonical = json.dumps(
        data,
        default=_json_default,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _slug(public_name: str, actor_id: uuid.UUID) -> str:
    base = slugify(public_name)[:130].strip("-") or "ponto-de-apoio"
    return f"{base}-{actor_id.hex[:8]}"


def create_support_point(
    *, user, data: dict[str, object], idempotency_key: uuid.UUID, request_id
) -> SupportPointCreationResult:
    fingerprint = request_fingerprint(data)
    now = timezone.now()

    try:
        with transaction.atomic():
            existing = (
                SupportPointIdempotencyRecord.objects.select_for_update()
                .filter(idempotency_key=idempotency_key)
                .first()
            )
            if existing is not None:
                if (
                    existing.created_by_id == user.pk
                    and existing.request_fingerprint == fingerprint
                    and existing.expires_at > now
                ):
                    return SupportPointCreationResult(existing.response_payload, True)
                raise SupportPointCreationConflict(
                    "A chave de idempotência já foi usada em outra operação.",
                    code="idempotency_conflict",
                )

            relations = resolve_support_point_relations(user=user, data=data, for_update=True)
            reject_support_point_duplicates(
                region=relations.region,
                public_name=data["actor"]["public_name"],
                address_fields=data["location"]["address_fields"],
                point=relations.point,
                contacts=data["contacts"],
            )

            actor_id = uuid.uuid4()
            actor_data = data["actor"]
            actor = Actor.objects.create(
                id=actor_id,
                external_id=f"manual:{actor_id}",
                actor_kind=Actor.ActorKind.SUPPORT,
                category=relations.category,
                slug=_slug(actor_data["public_name"], actor_id),
                public_name=actor_data["public_name"],
                legal_name=actor_data.get("legal_name", ""),
                short_description=actor_data["short_description"],
                full_description=actor_data.get("full_description", ""),
                services=actor_data.get("services", []),
                editorial_status=EditorialStatus.DRAFT,
                partnership_type=Actor.PartnershipType.EDITORIAL,
            )
            location_data = data["location"]
            location = ActorLocation.objects.create(
                actor=actor,
                region=relations.region,
                label=location_data["label"],
                address_fields=location_data["address_fields"],
                point=relations.point,
                is_primary=True,
                public_visibility=location_data["public_visibility"],
            )
            contacts = [
                ContactChannel.objects.create(
                    actor=actor,
                    channel_type=item["channel_type"],
                    public_value=item["value"],
                    value_encrypted="",
                    is_public=True,
                    source_type=item["source_type"],
                    source_reference=item["source_reference"],
                    verified_at=item["verified_at"],
                    verified_by=user,
                )
                for item in data["contacts"]
            ]
            links = [
                RouteActor.objects.create(
                    actor=actor,
                    route=relations.routes[item["route_id"]],
                    stage=relations.stages.get(item.get("stage_id")),
                    route_role=item["route_role"],
                    editorial_position=item["editorial_position"],
                    is_featured=item["is_featured"],
                    sponsorship_label=item["sponsorship_label"],
                )
                for item in data["route_links"]
            ]
            payload = {
                "id": str(actor.pk),
                "actor_kind": Actor.ActorKind.SUPPORT,
                "location_id": str(location.pk),
                "editorial_status": EditorialStatus.DRAFT,
                "partnership_type": Actor.PartnershipType.EDITORIAL,
                "region_id": str(relations.region.pk),
                "contact_ids": [str(item.pk) for item in contacts],
                "route_links": [
                    {
                        "id": str(item.pk),
                        "route_id": str(item.route_id),
                        "stage_id": str(item.stage_id) if item.stage_id else None,
                    }
                    for item in links
                ],
                "created_at": actor.created_at.isoformat(),
            }
            SupportPointIdempotencyRecord.objects.create(
                idempotency_key=idempotency_key,
                created_by=user,
                region=relations.region,
                actor=actor,
                request_fingerprint=fingerprint,
                response_payload=payload,
                expires_at=now + IDEMPOTENCY_TTL,
            )
            record_audit_event(
                actor=user,
                action=AuditEvent.Action.SUPPORT_POINT_CREATE,
                target_type="catalog_actor",
                target_id=actor.pk,
                request_id=request_id,
                region=relations.region,
                metadata={
                    "location_id": str(location.pk),
                    "contact_ids": payload["contact_ids"],
                    "route_link_ids": [item["id"] for item in payload["route_links"]],
                    "contact_count": len(contacts),
                    "route_link_count": len(links),
                    "idempotency_key": str(idempotency_key),
                    "idempotent_replay": False,
                },
            )
            return SupportPointCreationResult(payload, False)
    except IntegrityError as error:
        raise SupportPointCreationConflict(
            "A operação conflitou com um cadastro concorrente.",
            code="concurrent_conflict",
        ) from error
