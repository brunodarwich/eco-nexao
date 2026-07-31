from rest_framework import serializers


class GooglePlacesPreviewRequestSerializer(serializers.Serializer):
    region_slug = serializers.SlugField(max_length=120)
    route_slug = serializers.SlugField(max_length=120)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    radius_meters = serializers.IntegerField(min_value=1, max_value=50_000)
    included_types = serializers.ListField(
        child=serializers.SlugField(max_length=80),
        min_length=1,
        max_length=20,
    )
    max_results = serializers.IntegerField(min_value=1, max_value=20)

    def validate_included_types(self, value):
        return list(dict.fromkeys(value))


class GooglePlacesCandidateSerializer(serializers.Serializer):
    place_id = serializers.CharField()
    display_name = serializers.CharField(allow_blank=True)
    formatted_address = serializers.CharField(allow_blank=True)
    latitude = serializers.FloatField(allow_null=True)
    longitude = serializers.FloatField(allow_null=True)
    primary_type = serializers.CharField(allow_blank=True)
    google_maps_uri = serializers.URLField(allow_blank=True)


class GooglePlacesPreviewResponseSerializer(serializers.Serializer):
    run_id = serializers.UUIDField()
    provider = serializers.CharField()
    attribution = serializers.CharField()
    result_count = serializers.IntegerField()
    candidates = GooglePlacesCandidateSerializer(many=True)


class ExternalDiscoveryErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    field_errors = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))
    request_id = serializers.UUIDField()
