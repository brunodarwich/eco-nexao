from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_id = serializers.CharField(read_only=True)
    region_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = AuditEvent
        fields = (
            "id",
            "actor_id",
            "region_id",
            "action",
            "target_type",
            "target_id",
            "request_id",
            "reason",
            "metadata",
            "result",
            "occurred_at",
        )
        read_only_fields = fields


class AuditEventFilterSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=AuditEvent.Action.choices,
        required=False,
    )
    region_id = serializers.UUIDField(required=False)
    target_type = serializers.CharField(max_length=64, required=False)
    target_id = serializers.CharField(max_length=128, required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=50)
    offset = serializers.IntegerField(min_value=0, default=0)
