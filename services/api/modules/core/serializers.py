import json

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(
    {
        "type": "object",
        "required": ["type", "coordinates"],
        "properties": {
            "type": {"type": "string", "enum": ["Point"]},
            "coordinates": {
                "type": "array",
                "items": {"type": "number", "format": "double"},
                "minItems": 2,
            },
        },
    }
)
class PointGeoJSONField(serializers.Field):
    def to_representation(self, value):
        return json.loads(value.geojson)


@extend_schema_field(
    {
        "type": "object",
        "required": ["type", "coordinates"],
        "properties": {
            "type": {"type": "string", "enum": ["LineString"]},
            "coordinates": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {"type": "number", "format": "double"},
                    "minItems": 2,
                },
                "minItems": 2,
            },
        },
    }
)
class LineStringGeoJSONField(serializers.Field):
    def to_representation(self, value):
        return json.loads(value.geojson)
