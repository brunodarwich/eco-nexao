from dataclasses import dataclass
from typing import NoReturn

from django.contrib.gis.geos import Point
from django.contrib.gis.geos.error import GEOSException
from rest_framework import serializers

from modules.regions.models import Region
from modules.routes.models import Route, RouteStage

from .admin_permissions import require_support_point_region_access
from .models import Category


@dataclass(frozen=True)
class ResolvedSupportPointRelations:
    category: Category
    region: object
    routes: dict[object, Route]
    stages: dict[object, RouteStage]
    point: Point


def _relation_error(field: str, message: str, *, code: str = "invalid_relation") -> NoReturn:
    raise serializers.ValidationError({field: [message]}, code=code)


def resolve_support_point_relations(
    *, user, data, for_update: bool = False
) -> ResolvedSupportPointRelations:
    category_query = Category.objects.filter(pk=data["actor"]["category_id"], is_active=True)
    if for_update:
        category_query = category_query.select_for_update()
    category = category_query.first()
    if category is None:
        _relation_error("actor.category_id", "Categoria inválida ou inativa.")

    route_ids = {link["route_id"] for link in data["route_links"]}
    route_query = Route.objects.filter(pk__in=route_ids).select_related("region").order_by("pk")
    if for_update:
        route_query = route_query.select_for_update()
    routes = {route.pk: route for route in route_query}
    if set(routes) != route_ids:
        _relation_error("route_links", "Uma ou mais relações são inválidas.")

    region_ids = {route.region_id for route in routes.values()}
    if len(region_ids) != 1:
        _relation_error("route_links", "Todas as rotas devem pertencer à mesma região.")
    region = next(iter(routes.values())).region
    if for_update:
        region = Region.objects.select_for_update().get(pk=region.pk)
    require_support_point_region_access(user, region)

    if region.boundary is None or region.boundary.empty or not region.boundary.valid:
        _relation_error(
            "location",
            "A região ainda não possui limite geográfico verificável.",
            code="region_boundary_unavailable",
        )

    location = data["location"]
    point = Point(location["longitude"], location["latitude"], srid=4326)
    try:
        covered = region.boundary.covers(point)
    except GEOSException:
        _relation_error(
            "location",
            "A região ainda não possui limite geográfico verificável.",
            code="region_boundary_unavailable",
        )
    if not covered:
        _relation_error(
            "location",
            "As coordenadas não pertencem à região das rotas.",
            code="coordinate_outside_region",
        )

    stage_ids = {link["stage_id"] for link in data["route_links"] if link.get("stage_id")}
    stage_query = RouteStage.objects.filter(pk__in=stage_ids).order_by("pk")
    if for_update:
        stage_query = stage_query.select_for_update()
    stages = {stage.pk: stage for stage in stage_query}
    if set(stages) != stage_ids:
        _relation_error("route_links", "Uma ou mais relações são inválidas.")
    for link in data["route_links"]:
        stage_id = link.get("stage_id")
        if stage_id and stages[stage_id].route_id != link["route_id"]:
            _relation_error("route_links", "Uma ou mais relações são inválidas.")

    return ResolvedSupportPointRelations(
        category=category,
        region=region,
        routes=routes,
        stages=stages,
        point=point,
    )
