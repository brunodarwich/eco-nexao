from rest_framework import serializers

from .models import EditorialRevision, PublicationVersion
from .workflow import EditorialWorkflowError, validate_snapshot


class EditorialRevisionSerializer(serializers.ModelSerializer):
    created_by_id = serializers.CharField(read_only=True)
    updated_by_id = serializers.CharField(read_only=True)
    submitted_by_id = serializers.CharField(read_only=True, allow_null=True)
    reviewed_by_id = serializers.CharField(read_only=True, allow_null=True)
    region_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = EditorialRevision
        fields = (
            "id",
            "region_id",
            "target_type",
            "target_id",
            "sequence",
            "status",
            "base_snapshot",
            "snapshot",
            "diff",
            "lock_version",
            "created_by_id",
            "updated_by_id",
            "submitted_by_id",
            "submitted_at",
            "reviewed_by_id",
            "reviewed_at",
            "return_reason",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CreateEditorialRevisionSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=EditorialRevision.TargetType.choices)
    target_id = serializers.UUIDField()
    region_id = serializers.UUIDField(required=False, allow_null=True)
    snapshot = serializers.JSONField()

    def validate_snapshot(self, value):
        try:
            return validate_snapshot(value)
        except EditorialWorkflowError as error:
            raise serializers.ValidationError(error.field_errors["snapshot"]) from error


class UpdateEditorialRevisionSerializer(serializers.Serializer):
    snapshot = serializers.JSONField()
    lock_version = serializers.IntegerField(min_value=1)

    def validate_snapshot(self, value):
        try:
            return validate_snapshot(value)
        except EditorialWorkflowError as error:
            raise serializers.ValidationError(error.field_errors["snapshot"]) from error


class RevisionTransitionSerializer(serializers.Serializer):
    lock_version = serializers.IntegerField(min_value=1)


class ReturnEditorialRevisionSerializer(RevisionTransitionSerializer):
    reason = serializers.CharField(max_length=2000, trim_whitespace=True)


class PublishEditorialRevisionSerializer(RevisionTransitionSerializer):
    reason = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        required=False,
        allow_blank=True,
    )
    source_confirmed = serializers.BooleanField()
    human_confirmed = serializers.BooleanField()
    critical_information_current = serializers.BooleanField()
    critical_override_reason = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        required=False,
        allow_blank=True,
    )


class RestorePublicationVersionSerializer(serializers.Serializer):
    expected_current_version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(
        max_length=2000,
        min_length=20,
        trim_whitespace=True,
    )
    source_confirmed = serializers.BooleanField()
    human_confirmed = serializers.BooleanField()
    critical_information_current = serializers.BooleanField()
    critical_override_reason = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        required=False,
        allow_blank=True,
    )


class PublicationVersionSerializer(serializers.ModelSerializer):
    revision_id = serializers.UUIDField(read_only=True, allow_null=True)
    restored_from_id = serializers.UUIDField(read_only=True, allow_null=True)
    region_id = serializers.UUIDField(read_only=True)
    approved_by_id = serializers.CharField(read_only=True)
    published_by_id = serializers.CharField(read_only=True)

    class Meta:
        model = PublicationVersion
        fields = (
            "id",
            "revision_id",
            "restored_from_id",
            "region_id",
            "target_type",
            "target_id",
            "version",
            "snapshot",
            "checksum",
            "approved_by_id",
            "published_by_id",
            "reason",
            "source_confirmed",
            "human_confirmed",
            "critical_information_current",
            "critical_override_reason",
            "published_at",
        )
        read_only_fields = fields


class EditorialWorkflowErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    field_errors = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))
    request_id = serializers.UUIDField()
