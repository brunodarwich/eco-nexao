from django.db.models import Prefetch, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from modules.catalog.models import ActorLocation, ContactChannel, RouteActor
from modules.core.models import EditorialStatus

from .models import Alert, Route
from .serializers import (
    RouteCatalogItemSerializer,
    RouteDetailSerializer,
    RouteSummarySerializer,
)


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
