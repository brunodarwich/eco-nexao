from django.db.models import Prefetch, Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.accounts.permissions import (
    AdminAction,
    AdminRole,
    get_user_region_slugs,
    get_user_roles,
    has_admin_action,
)
from modules.catalog.models import ActorLocation, ContactChannel, RouteActor
from modules.core.models import EditorialStatus

from .admin_serializers import RegionRouteReadinessResponseSerializer
from .models import Alert, Route
from .readiness import calculate_route_readiness
from .serializers import (
    RouteCatalogItemSerializer,
    RouteDetailSerializer,
    RouteSummarySerializer,
)
from .throttles import AdminReadinessThrottle


class PublishedRouteQuerysetMixin:
    def get_queryset(self):
        return Route.objects.filter(
            region__slug=self.kwargs["region_slug"],
            region__status=EditorialStatus.PUBLISHED,
            editorial_status=EditorialStatus.PUBLISHED,
        )


class RegionRouteListView(PublishedRouteQuerysetMixin, generics.ListAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = RouteSummarySerializer

    @extend_schema(
        operation_id="listPublishedRegionRoutes",
        summary="Listar rotas publicadas de uma região",
        tags=["Routes"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RouteDetailView(PublishedRouteQuerysetMixin, generics.RetrieveAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = RouteDetailSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "route_slug"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("region")
            .prefetch_related(
                "stages",
                "segments",
                Prefetch(
                    "alerts",
                    queryset=Alert.objects.filter(
                        status=EditorialStatus.PUBLISHED,
                        starts_at__lte=timezone.now(),
                    ).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())),
                ),
            )
        )

    @extend_schema(
        operation_id="retrievePublishedRoute",
        summary="Obter uma rota publicada",
        tags=["Routes"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RouteCatalogListView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = RouteCatalogItemSerializer

    def get_queryset(self):
        public_locations = ActorLocation.objects.filter(
            region__slug=self.kwargs["region_slug"],
            public_visibility=True,
        ).prefetch_related("operating_hours")
        public_contacts = ContactChannel.objects.filter(is_public=True).exclude(public_value="")
        return (
            RouteActor.objects.filter(
                route__region__slug=self.kwargs["region_slug"],
                route__region__status=EditorialStatus.PUBLISHED,
                route__slug=self.kwargs["route_slug"],
                route__editorial_status=EditorialStatus.PUBLISHED,
                actor__editorial_status=EditorialStatus.PUBLISHED,
                actor__category__is_active=True,
            )
            .select_related("actor", "actor__category")
            .prefetch_related(
                Prefetch(
                    "actor__locations",
                    queryset=public_locations,
                    to_attr="public_locations",
                ),
                Prefetch(
                    "actor__contact_channels",
                    queryset=public_contacts,
                    to_attr="public_contact_channels",
                ),
            )
        )

    @extend_schema(
        operation_id="listPublishedRouteCatalog",
        summary="Listar o catálogo público contextual da rota",
        description=(
            "Retorna somente atores publicados, localizações visíveis na região "
            "e contatos autorizados para publicação."
        ),
        tags=["Catalog"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema(
    parameters=[OpenApiParameter("region_slug", str, required=True)],
    responses={
        200: RegionRouteReadinessResponseSerializer,
        400: {"type": "object", "additionalProperties": True},
        401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        403: {"type": "object", "properties": {"detail": {"type": "string"}}},
        429: {"type": "object", "properties": {"detail": {"type": "string"}}},
        500: {"type": "object", "properties": {"detail": {"type": "string"}}},
    },
    operation_id="listAdminRouteReadiness",
    tags=["Admin routes"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([AdminReadinessThrottle])
def admin_route_readiness(request):
    """DTO operacional, deliberadamente separado de contratos públicos de rota."""
    if not has_admin_action(request.user, AdminAction.VIEW_AGGREGATES):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)
    region_slug = request.query_params.get("region_slug", "")
    if not region_slug:
        return Response(
            {"detail": "region_slug é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
        )
    if AdminRole.ADMINISTRATOR not in get_user_roles(
        request.user
    ) and region_slug not in get_user_region_slugs(request.user):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)
    routes = (
        Route.objects.filter(region__slug=region_slug)
        .select_related("region")
        .prefetch_related("stages", "segments", "actor_links__actor", "alerts")
    )
    items = [calculate_route_readiness(route).payload for route in routes]
    response = Response({"region_slug": region_slug, "routes": items})
    response["Cache-Control"] = "no-store"
    return response
