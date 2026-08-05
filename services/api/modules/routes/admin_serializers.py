from rest_framework import serializers

from modules.core.models import EditorialStatus


class ReadinessDimensionsSerializer(serializers.Serializer):
    content = serializers.IntegerField(min_value=0, max_value=100)
    trace = serializers.IntegerField(min_value=0, max_value=100)
    catalog = serializers.IntegerField(min_value=0, max_value=100)
    alerts = serializers.IntegerField(min_value=0, max_value=100)
    offline = serializers.IntegerField(min_value=0, max_value=100)


class RouteReadinessSerializer(serializers.Serializer):
    route_id = serializers.UUIDField()
    slug = serializers.CharField()
    title = serializers.CharField()
    editorial_status = serializers.ChoiceField(choices=EditorialStatus.choices)
    formula_version = serializers.CharField()
    weights = ReadinessDimensionsSerializer()
    dimensions = ReadinessDimensionsSerializer()
    score = serializers.IntegerField(min_value=0, max_value=100, allow_null=True)
    is_ready = serializers.BooleanField()
    blocking_reasons = serializers.ListField(child=serializers.CharField())
    missing_required_fields = serializers.ListField(child=serializers.CharField())
    stages_count = serializers.IntegerField(min_value=0)
    segments_count = serializers.IntegerField(min_value=0)
    published_points_count = serializers.IntegerField(min_value=0)
    points_in_review_count = serializers.IntegerField(min_value=0)
    verified_contacts_count = serializers.IntegerField(min_value=0)
    unverified_public_contacts_count = serializers.IntegerField(min_value=0)
    blocking_alerts_count = serializers.IntegerField(min_value=0)
    last_revision_at = serializers.DateTimeField(allow_null=True)
    published_version = serializers.IntegerField(min_value=1, allow_null=True)


class RegionRouteReadinessResponseSerializer(serializers.Serializer):
    region_slug = serializers.CharField()
    routes = RouteReadinessSerializer(many=True)
