from django.contrib.gis.db.models import (
    LineStringField,
    MultiPolygonField,
    PointField,
)
from django.db.models import CASCADE, PROTECT, SET_NULL

from modules.catalog.models import ActorLocation, RouteActor
from modules.regions.models import Region
from modules.routes.models import Alert, Route, RouteSegment, RouteStage


def constraint_names(model: type) -> set[str]:
    return {constraint.name for constraint in model._meta.constraints}


def test_spatial_fields_use_wgs84_and_spatial_indexes():
    spatial_fields = (
        Region._meta.get_field("boundary"),
        Region._meta.get_field("center_point"),
        RouteStage._meta.get_field("point"),
        RouteSegment._meta.get_field("geometry"),
        ActorLocation._meta.get_field("point"),
        ActorLocation._meta.get_field("service_area"),
    )

    assert isinstance(spatial_fields[0], MultiPolygonField)
    assert isinstance(spatial_fields[1], PointField)
    assert isinstance(spatial_fields[3], LineStringField)
    assert all(field.srid == 4326 for field in spatial_fields)
    assert all(field.spatial_index for field in spatial_fields)


def test_multiregional_constraints_are_declared():
    assert "route_region_slug_uniq" in constraint_names(Route)
    assert "location_actor_region_label_uniq" in constraint_names(ActorLocation)
    assert "location_one_primary_per_region" in constraint_names(ActorLocation)


def test_route_structure_constraints_are_declared():
    assert {
        "stage_route_position_uniq",
        "stage_position_positive",
        "stage_duration_positive",
    } <= constraint_names(RouteStage)
    assert {
        "segment_path_uniq",
        "segment_distinct_stages",
        "segment_distance_positive",
        "segment_duration_positive",
    } <= constraint_names(RouteSegment)
    assert {
        "route_actor_context_uniq",
        "route_actor_position_positive",
    } <= constraint_names(RouteActor)


def test_referential_delete_policies_preserve_editorial_integrity():
    assert Route._meta.get_field("region").remote_field.on_delete is PROTECT
    assert RouteStage._meta.get_field("route").remote_field.on_delete is CASCADE
    assert RouteSegment._meta.get_field("route").remote_field.on_delete is CASCADE
    assert RouteSegment._meta.get_field("from_stage").remote_field.on_delete is PROTECT
    assert RouteSegment._meta.get_field("to_stage").remote_field.on_delete is PROTECT
    assert Alert._meta.get_field("route").remote_field.on_delete is CASCADE
    assert ActorLocation._meta.get_field("region").remote_field.on_delete is PROTECT
    assert RouteActor._meta.get_field("route").remote_field.on_delete is CASCADE
    assert RouteActor._meta.get_field("stage").remote_field.on_delete is SET_NULL
