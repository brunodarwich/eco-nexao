from rest_framework import serializers

from modules.catalog.models import Actor, ActorLocation, ContactChannel, OperatingHours, RouteActor
from modules.core.serializers import LineStringGeoJSONField, PointGeoJSONField

from .models import Alert, Route, RouteSegment, RouteStage


class RouteSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = (
            "id",
            "slug",
            "public_name",
            "short_promise",
            "duration_minutes",
            "difficulty",
            "estimated_cost_min",
            "estimated_cost_max",
            "transport_modes",
            "accessibility_content",
            "offline_enabled",
            "updated_at",
        )


class RouteStageSerializer(serializers.ModelSerializer):
    point = PointGeoJSONField(read_only=True)

    class Meta:
        model = RouteStage
        fields = (
            "id",
            "position",
            "public_name",
            "description",
            "point",
            "arrival_guidance",
            "duration_minutes",
            "stage_type",
            "is_optional",
            "updated_at",
        )


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = (
            "id",
            "severity",
            "title",
            "description",
            "alternative",
            "starts_at",
            "ends_at",
            "updated_at",
        )


class RouteSegmentSerializer(serializers.ModelSerializer):
    geometry = LineStringGeoJSONField(read_only=True)

    class Meta:
        model = RouteSegment
        fields = (
            "id",
            "from_stage_id",
            "to_stage_id",
            "geometry",
            "transport_mode",
            "distance_meters",
            "duration_minutes",
            "instructions",
            "updated_at",
        )


class RouteDetailSerializer(RouteSummarySerializer):
    stages = RouteStageSerializer(many=True, read_only=True)
    segments = RouteSegmentSerializer(many=True, read_only=True)
    alerts = AlertSerializer(many=True, read_only=True)
    region_slug = serializers.SlugField(source="region.slug", read_only=True)
    region_name = serializers.CharField(source="region.public_name", read_only=True)

    class Meta(RouteSummarySerializer.Meta):
        fields = RouteSummarySerializer.Meta.fields + (
            "region_slug",
            "region_name",
            "description",
            "preparation_content",
            "stages",
            "segments",
            "alerts",
        )


class OperatingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatingHours
        fields = (
            "weekday",
            "opens_at",
            "closes_at",
            "is_closed",
            "exception_date",
            "public_note",
        )


class PublicActorLocationSerializer(serializers.ModelSerializer):
    point = PointGeoJSONField(read_only=True, allow_null=True)
    operating_hours = OperatingHoursSerializer(many=True, read_only=True)

    class Meta:
        model = ActorLocation
        fields = (
            "label",
            "address_fields",
            "point",
            "is_primary",
            "operating_hours",
            "updated_at",
        )


class PublicContactChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactChannel
        fields = ("channel_type", "public_value", "verified_at")


class PublicActorSerializer(serializers.ModelSerializer):
    category_slug = serializers.SlugField(source="category.slug", read_only=True)
    category_name = serializers.CharField(source="category.public_name", read_only=True)
    locations = PublicActorLocationSerializer(
        source="public_locations",
        many=True,
        read_only=True,
    )
    contact_channels = PublicContactChannelSerializer(
        source="public_contact_channels",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Actor
        fields = (
            "id",
            "slug",
            "public_name",
            "actor_kind",
            "short_description",
            "full_description",
            "services",
            "partnership_type",
            "category_slug",
            "category_name",
            "locations",
            "contact_channels",
            "updated_at",
        )


class RouteCatalogItemSerializer(serializers.ModelSerializer):
    actor = PublicActorSerializer(read_only=True)
    stage_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = RouteActor
        fields = (
            "route_role",
            "editorial_position",
            "is_featured",
            "sponsorship_label",
            "stage_id",
            "actor",
        )
