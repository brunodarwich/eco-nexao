from rest_framework import serializers

from modules.core.serializers import PointGeoJSONField

from .models import Region


class RegionSummarySerializer(serializers.ModelSerializer):
    center_point = PointGeoJSONField(read_only=True)

    class Meta:
        model = Region
        fields = (
            "id",
            "slug",
            "public_name",
            "short_description",
            "center_point",
            "timezone",
            "published_version",
            "updated_at",
        )
