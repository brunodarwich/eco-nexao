from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from drf_spectacular.utils import extend_schema
from rest_framework import status
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

from .models import DailyAnalyticsAggregate, RawAnalyticsEvent
from .serializers import AnalyticsBatchSerializer
from .throttles import AnalyticsBatchThrottle


@extend_schema(
    request=AnalyticsBatchSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {"received": {"type": "integer"}, "status": {"type": "string"}},
        },
        400: {"type": "object", "additionalProperties": True},
        429: {"type": "object", "properties": {"detail": {"type": "string"}}},
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnalyticsBatchThrottle])
def public_event_batch(request):
    """
    Ingestão pública em lote de eventos de analytics pseudonimizados.
    Aplica allowlist estrita e rejeição de dados pessoais ou coordenadas.
    """
    serializer = AnalyticsBatchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    events_data = serializer.validated_data["events"]

    with transaction.atomic():
        created_events = []
        for item in events_data:
            event = RawAnalyticsEvent(**item)
            created_events.append(event)

            # Atualizar ou criar agregação diária de forma atômica no banco de dados
            occurred_date = event.occurred_at.date()
            region_slug = event.region_id or ""
            route_slug = event.route_id or ""

            updated_count = DailyAnalyticsAggregate.objects.filter(
                date=occurred_date,
                event_name=event.event_name,
                region_slug=region_slug,
                route_slug=route_slug,
            ).update(count=F("count") + 1)

            if not updated_count:
                try:
                    DailyAnalyticsAggregate.objects.create(
                        date=occurred_date,
                        event_name=event.event_name,
                        region_slug=region_slug,
                        route_slug=route_slug,
                        count=1,
                    )
                except IntegrityError:
                    DailyAnalyticsAggregate.objects.filter(
                        date=occurred_date,
                        event_name=event.event_name,
                        region_slug=region_slug,
                        route_slug=route_slug,
                    ).update(count=F("count") + 1)

        RawAnalyticsEvent.objects.bulk_create(created_events)

    return Response(
        {"received": len(created_events), "status": "processed"},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    responses={
        200: {
            "type": "object",
            "properties": {
                "total_events": {"type": "integer"},
                "aggregates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "event_name": {"type": "string"},
                            "region_slug": {"type": "string"},
                            "route_slug": {"type": "string"},
                            "count": {"type": "integer"},
                        },
                    },
                },
            },
        },
        401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        403: {"type": "object", "properties": {"detail": {"type": "string"}}},
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_analytics_summary(request):
    """
    Visão resumida de analytics agregada para o painel administrativo.
    Protegido por autenticação e livre de identificadores individuais.
    """
    if not (
        has_admin_action(request.user, AdminAction.VIEW_AGGREGATES)
        or has_admin_action(request.user, AdminAction.VIEW_ANALYTICS)
    ):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)

    qs = DailyAnalyticsAggregate.objects.all().order_by("-date", "-count")

    roles = get_user_roles(request.user)
    if AdminRole.ADMINISTRATOR not in roles:
        allowed_slugs = get_user_region_slugs(request.user)
        qs = qs.filter(region_slug__in=allowed_slugs)

    region_filter = request.query_params.get("region_slug")
    route_filter = request.query_params.get("route_slug")
    if region_filter:
        qs = qs.filter(region_slug=region_filter)
    if route_filter:
        qs = qs.filter(route_slug=route_filter)

    total_events = qs.aggregate(total=Sum("count"))["total"] or 0
    aggregates_data = [
        {
            "date": str(item.date),
            "event_name": item.event_name,
            "region_slug": item.region_slug,
            "route_slug": item.route_slug,
            "count": item.count,
        }
        for item in qs[:100]
    ]

    return Response(
        {
            "total_events": total_events,
            "aggregates": aggregates_data,
        },
        status=status.HTTP_200_OK,
    )
