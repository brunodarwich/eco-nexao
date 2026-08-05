import json

from django.contrib.gis.geos import LineString, Point
from drf_spectacular.generators import SchemaGenerator

from modules.core.serializers import LineStringGeoJSONField, PointGeoJSONField
from modules.regions.views import RegionListView

from .serializers import (
    PublicActorSerializer,
    PublicContactChannelSerializer,
    RouteCatalogItemSerializer,
)
from .views import RegionRouteListView, RouteCatalogListView, RouteDetailView

PUBLIC_PATHS = {
    "/api/v1/regions",
    "/api/v1/regions/{region_slug}/routes",
    "/api/v1/regions/{region_slug}/routes/{route_slug}",
    "/api/v1/regions/{region_slug}/routes/{route_slug}/catalog",
}


def test_openapi_publishes_multiregional_read_contract():
    schema = SchemaGenerator().get_schema(request=None, public=True)

    assert PUBLIC_PATHS.issubset(schema["paths"])
    assert (
        schema["paths"]["/api/v1/regions/{region_slug}/routes"]["get"]["operationId"]
        == "listPublishedRegionRoutes"
    )
    assert (
        schema["paths"]["/api/v1/regions/{region_slug}/routes/{route_slug}"]["get"]["operationId"]
        == "retrievePublishedRoute"
    )
    for path in PUBLIC_PATHS:
        assert schema["paths"][path]["get"].get("security") in (None, [])


def test_openapi_does_not_expose_private_catalog_fields():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    public_paths_text = json.dumps({path: schema["paths"][path] for path in PUBLIC_PATHS})

    for private_field in (
        "external_source_references",
        "legal_name",
        "provider_record_id",
        "review_status",
        "value_encrypted",
        "source_reference",
        "verified_by",
        "external_id",
    ):
        assert private_field not in public_paths_text


def test_public_serializers_keep_explicit_allowlists():
    assert "legal_name" not in PublicActorSerializer.Meta.fields
    assert "external_id" not in PublicActorSerializer.Meta.fields
    assert "external_source_references" not in PublicActorSerializer.Meta.fields
    assert "value_encrypted" not in PublicContactChannelSerializer.Meta.fields
    assert "source_reference" not in PublicContactChannelSerializer.Meta.fields
    assert "verified_by" not in PublicContactChannelSerializer.Meta.fields
    assert "public_value" in PublicContactChannelSerializer.Meta.fields
    assert RouteCatalogItemSerializer.Meta.fields == (
        "route_role",
        "editorial_position",
        "is_featured",
        "sponsorship_label",
        "stage_id",
        "actor",
    )


def test_point_field_outputs_geojson_in_wgs84_order():
    representation = PointGeoJSONField().to_representation(Point(-54.7081, -2.4385, srid=4326))

    assert representation == {
        "type": "Point",
        "coordinates": [-54.7081, -2.4385],
    }


def test_line_field_outputs_geojson_in_wgs84_order():
    representation = LineStringGeoJSONField().to_representation(
        LineString((-54.97478, -2.55997), (-54.96111, -2.55833), srid=4326)
    )

    assert representation == {
        "type": "LineString",
        "coordinates": [[-54.97478, -2.55997], [-54.96111, -2.55833]],
    }


def test_public_querysets_require_published_region_and_content():
    region_filters = repr(RegionListView.queryset.query.where).lower()
    assert "status" in region_filters
    assert "published" in region_filters

    route_list = RegionRouteListView()
    route_list.kwargs = {"region_slug": "regiao-a"}
    route_filters = repr(route_list.get_queryset().query.where).lower()
    assert "regiao-a" in route_filters
    assert route_filters.count("published") == 2

    route_detail = RouteDetailView()
    route_detail.kwargs = {"region_slug": "regiao-b", "route_slug": "rota-1"}
    detail_filters = repr(route_detail.get_queryset().query.where).lower()
    assert "regiao-b" in detail_filters
    assert detail_filters.count("published") == 2
    alert_prefetch = next(
        lookup
        for lookup in route_detail.get_queryset()._prefetch_related_lookups
        if getattr(lookup, "prefetch_to", None) == "alerts"
    )
    alert_filters = repr(alert_prefetch.queryset.query.where).lower()
    assert "starts_at" in alert_filters
    assert "ends_at" in alert_filters

    catalog = RouteCatalogListView()
    catalog.kwargs = {"region_slug": "regiao-c", "route_slug": "rota-2"}
    catalog_filters = repr(catalog.get_queryset().query.where).lower()
    assert "regiao-c" in catalog_filters
    assert "rota-2" in catalog_filters
    assert catalog_filters.count("published") == 3
    assert "true" in catalog_filters
    assert all(
        "external_source_references" not in str(lookup)
        for lookup in catalog.get_queryset()._prefetch_related_lookups
    )
