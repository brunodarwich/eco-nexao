from dataclasses import dataclass

from django.db.models import Max, Q
from django.utils import timezone

from modules.catalog.models import ContactChannel
from modules.core.models import EditorialStatus
from modules.publishing.models import EditorialRevision, PublicationVersion

from .models import Alert, Route

READINESS_FORMULA_VERSION = "1.0"
READINESS_WEIGHTS = {
    "content": 30,
    "trace": 25,
    "catalog": 20,
    "alerts": 15,
    "offline": 10,
}
CONTENT_FIELDS = (
    "public_name",
    "short_promise",
    "description",
    "duration_minutes",
    "difficulty",
    "transport_modes",
    "preparation_content",
)


@dataclass(frozen=True)
class ReadinessResult:
    payload: dict


def _has_value(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | tuple | dict):
        return bool(value)
    return value is not None


def calculate_route_readiness(route: Route) -> ReadinessResult:
    now = timezone.now()
    stages_count = route.stages.count()
    segments_count = route.segments.count()
    missing_fields = [field for field in CONTENT_FIELDS if not _has_value(getattr(route, field))]
    active_blocking_alerts = (
        route.alerts.filter(
            status=EditorialStatus.PUBLISHED,
            severity=Alert.Severity.CRITICAL,
            starts_at__lte=now,
        )
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))
        .count()
    )

    links = list(route.actor_links.all())
    published_links = [
        link for link in links if link.actor.editorial_status == EditorialStatus.PUBLISHED
    ]
    linked_actor_ids = {link.actor_id for link in links}
    review_revision_actor_ids = set(
        EditorialRevision.objects.filter(
            region=route.region,
            target_type=EditorialRevision.TargetType.ACTOR,
            target_id__in=linked_actor_ids,
            status=EditorialRevision.Status.REVIEW,
        ).values_list("target_id", flat=True)
    )
    points_in_review_count = len(
        {
            link.actor_id
            for link in links
            if link.actor.editorial_status == EditorialStatus.REVIEW
            or link.actor_id in review_revision_actor_ids
        }
    )

    public_contacts = list(
        ContactChannel.objects.filter(
            actor_id__in=[link.actor_id for link in published_links],
            is_public=True,
        ).exclude(public_value="")
    )
    verified_contacts_count = sum(contact.verified_at is not None for contact in public_contacts)
    unverified_contacts_count = len(public_contacts) - verified_contacts_count
    actors_with_unverified = {
        contact.actor_id for contact in public_contacts if not contact.verified_at
    }
    verified_points = len(published_links) - len(actors_with_unverified)

    dimensions = {
        "content": round(100 * (len(CONTENT_FIELDS) - len(missing_fields)) / len(CONTENT_FIELDS)),
        "trace": round(100 * ((stages_count > 0) + (segments_count > 0)) / 2),
        "catalog": (
            100 if not published_links else round(100 * verified_points / len(published_links))
        ),
        "alerts": 0 if active_blocking_alerts else 100,
        "offline": 100 if route.offline_enabled else 0,
    }
    score = round(sum(dimensions[key] * READINESS_WEIGHTS[key] for key in READINESS_WEIGHTS) / 100)

    blockers = [f"missing_required_field:{field}" for field in missing_fields]
    if stages_count == 0:
        blockers.append("missing_stages")
    if segments_count == 0:
        blockers.append("missing_segments")
    if active_blocking_alerts:
        blockers.append("active_critical_alert")
    if unverified_contacts_count:
        blockers.append("unverified_public_contact")

    latest_revision = EditorialRevision.objects.filter(
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id=route.id,
    ).aggregate(value=Max("updated_at"))["value"]
    published_version = PublicationVersion.objects.filter(
        target_type=EditorialRevision.TargetType.ROUTE,
        target_id=route.id,
    ).aggregate(value=Max("version"))["value"]

    return ReadinessResult(
        {
            "route_id": route.id,
            "slug": route.slug,
            "title": route.public_name,
            "editorial_status": route.editorial_status,
            "formula_version": READINESS_FORMULA_VERSION,
            "weights": READINESS_WEIGHTS,
            "dimensions": dimensions,
            "score": score,
            "is_ready": not blockers,
            "blocking_reasons": blockers,
            "missing_required_fields": missing_fields,
            "stages_count": stages_count,
            "segments_count": segments_count,
            "published_points_count": len(published_links),
            "points_in_review_count": points_in_review_count,
            "verified_contacts_count": verified_contacts_count,
            "unverified_public_contacts_count": unverified_contacts_count,
            "blocking_alerts_count": active_blocking_alerts,
            "last_revision_at": latest_revision,
            "published_version": published_version,
        }
    )
