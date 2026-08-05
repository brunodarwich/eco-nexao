from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from modules.accounts.permissions import (
    AdminAction,
    AdminRole,
    get_user_region_slugs,
    get_user_roles,
    has_admin_action,
)
from modules.catalog.models import Actor, RouteActor
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Route

from .models import DailyAnalyticsAggregate, RawAnalyticsEvent
from .serializers import (
    ALLOWED_EVENTS,
    AnalyticsBatchResponseSerializer,
    AnalyticsBatchSerializer,
    AnalyticsSummaryResponseSerializer,
    OperationalAnalyticsResponseSerializer,
)
from .throttles import AdminAnalyticsThrottle, AnalyticsBatchThrottle

PRIVACY_THRESHOLD = 10


def _validate_domain_dimensions(events):
    errors = {}
    for index, item in enumerate(events):
        region_slug = item["region_id"]
        route_slug = item.get("route_id", "")
        region_exists = Region.objects.filter(
            slug=region_slug,
            status=EditorialStatus.PUBLISHED,
        ).exists()
        if not region_exists:
            errors[index] = {"region_id": "Região publicada não encontrada."}
            continue
        if (
            route_slug
            and not Route.objects.filter(
                region__slug=region_slug,
                slug=route_slug,
                editorial_status=EditorialStatus.PUBLISHED,
            ).exists()
        ):
            errors[index] = {"route_id": "Rota publicada não encontrada na região."}
            continue
        if (
            item["event_name"] == "contact_opened"
            and not RouteActor.objects.filter(
                route__region__slug=region_slug,
                route__slug=route_slug,
                actor_id=item["actor_id"],
                actor__editorial_status=EditorialStatus.PUBLISHED,
            ).exists()
        ):
            errors[index] = {"actor_id": "Ponto publicado não pertence à rota."}
    if errors:
        raise serializers.ValidationError({"events": errors})


@extend_schema(
    request=AnalyticsBatchSerializer,
    responses={
        201: AnalyticsBatchResponseSerializer,
        400: {"type": "object", "additionalProperties": True},
        409: {"type": "object", "properties": {"detail": {"type": "string"}}},
        429: {"type": "object", "properties": {"detail": {"type": "string"}}},
    },
    operation_id="createPublicAnalyticsBatch",
    tags=["Analytics"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnalyticsBatchThrottle])
def public_event_batch(request):
    serializer = AnalyticsBatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    events_data = serializer.validated_data["events"]
    _validate_domain_dimensions(events_data)

    try:
        with transaction.atomic():
            raw_events = [RawAnalyticsEvent(**item) for item in events_data]
            RawAnalyticsEvent.objects.bulk_create(raw_events)
            for event in raw_events:
                support_point_id = event.actor_id if event.event_name == "contact_opened" else ""
                lookup = {
                    "date": event.occurred_at.date(),
                    "event_name": event.event_name,
                    "region_slug": event.region_id,
                    "route_slug": event.route_id,
                    "support_point_id": support_point_id,
                }
                updated = DailyAnalyticsAggregate.objects.filter(**lookup).update(
                    count=F("count") + 1
                )
                if not updated:
                    try:
                        DailyAnalyticsAggregate.objects.create(**lookup, count=1)
                    except IntegrityError:
                        DailyAnalyticsAggregate.objects.filter(**lookup).update(
                            count=F("count") + 1
                        )
    except IntegrityError:
        return Response(
            {"detail": "Lote duplicado ou concorrente; nenhum evento foi processado."},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(
        {"received": len(events_data), "status": "processed"},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    responses={
        200: AnalyticsSummaryResponseSerializer,
        401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        403: {"type": "object", "properties": {"detail": {"type": "string"}}},
    },
    operation_id="retrieveAdminAnalyticsSummary",
    tags=["Admin analytics"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_analytics_summary(request):
    if not (
        has_admin_action(request.user, AdminAction.VIEW_AGGREGATES)
        or has_admin_action(request.user, AdminAction.VIEW_ANALYTICS)
    ):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)
    queryset = DailyAnalyticsAggregate.objects.all().order_by("-date", "-count")
    if AdminRole.ADMINISTRATOR not in get_user_roles(request.user):
        queryset = queryset.filter(region_slug__in=get_user_region_slugs(request.user))
    if region_slug := request.query_params.get("region_slug"):
        if AdminRole.ADMINISTRATOR not in get_user_roles(
            request.user
        ) and region_slug not in get_user_region_slugs(request.user):
            return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)
        queryset = queryset.filter(region_slug=region_slug)
    if route_slug := request.query_params.get("route_slug"):
        queryset = queryset.filter(route_slug=route_slug)
    total_events = queryset.aggregate(total=Sum("count"))["total"] or 0
    return Response(
        {
            "total_events": total_events,
            "aggregates": [
                {
                    "date": str(item.date),
                    "event_name": item.event_name,
                    "region_slug": item.region_slug,
                    "route_slug": item.route_slug,
                    "count": item.count,
                }
                for item in queryset[:100]
            ],
        }
    )


@extend_schema(
    parameters=[
        OpenApiParameter("region_slug", str, required=True),
        OpenApiParameter("route_slug", str, required=False),
        OpenApiParameter("start", str, required=False),
        OpenApiParameter("end", str, required=False),
    ],
    responses={
        200: OperationalAnalyticsResponseSerializer,
        400: {"type": "object", "additionalProperties": True},
        401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        403: {"type": "object", "properties": {"detail": {"type": "string"}}},
        429: {"type": "object", "properties": {"detail": {"type": "string"}}},
        500: {"type": "object", "properties": {"detail": {"type": "string"}}},
    },
    operation_id="retrieveAdminOperationalAnalytics",
    tags=["Admin analytics"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([AdminAnalyticsThrottle])
def admin_operational_analytics(request):
    if not has_admin_action(request.user, AdminAction.VIEW_ANALYTICS):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)
    region_slug = request.query_params.get("region_slug", "")
    route_slug = request.query_params.get("route_slug", "")
    today = timezone.localdate()
    start = parse_date(request.query_params.get("start", "")) or today - timedelta(days=29)
    end = parse_date(request.query_params.get("end", "")) or today
    if not region_slug:
        return Response(
            {"detail": "region_slug é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
        )
    if start > end or (end - start).days > 396:
        return Response({"detail": "Período inválido."}, status=status.HTTP_400_BAD_REQUEST)
    if AdminRole.ADMINISTRATOR not in get_user_roles(
        request.user
    ) and region_slug not in get_user_region_slugs(request.user):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)

    queryset = DailyAnalyticsAggregate.objects.filter(
        region_slug=region_slug,
        date__range=(start, end),
    )
    if route_slug:
        queryset = queryset.filter(route_slug=route_slug)
    totals = {
        row["event_name"]: row["total"]
        for row in queryset.values("event_name").annotate(total=Sum("count"))
    }
    metrics = [
        {
            "event_name": event_name,
            "count": total if (total := totals.get(event_name, 0)) >= PRIVACY_THRESHOLD else None,
            "suppressed": total < PRIVACY_THRESHOLD,
        }
        for event_name in sorted(ALLOWED_EVENTS)
    ]
    ranking_rows = list(
        queryset.filter(event_name="contact_opened")
        .exclude(support_point_id="")
        .values("support_point_id")
        .annotate(contacts=Sum("count"))
        .filter(contacts__gte=PRIVACY_THRESHOLD)
        .order_by("-contacts", "support_point_id")
    )
    actors = {
        str(actor_id): actor
        for actor_id, actor in Actor.objects.in_bulk(
            [row["support_point_id"] for row in ranking_rows]
        ).items()
    }
    ranking = [
        {
            "support_point_id": row["support_point_id"],
            "support_point_name": actors[row["support_point_id"]].public_name,
            "contacts": row["contacts"],
        }
        for row in ranking_rows
        if row["support_point_id"] in actors
    ]
    response = Response(
        {
            "region_slug": region_slug,
            "route_slug": route_slug,
            "start": start,
            "end": end,
            "privacy_threshold": PRIVACY_THRESHOLD,
            "metrics": metrics,
            "ranking": ranking,
        }
    )
    response["Cache-Control"] = "no-store"
    return response
