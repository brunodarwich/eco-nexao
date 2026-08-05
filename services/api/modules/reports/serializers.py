from rest_framework import serializers

from modules.accounts.permissions import (
    AdminAction,
    has_admin_action,
    resolve_object_region,
)
from modules.catalog.models import Actor
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Route

from .models import PublicReport


class PublicReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicReport
        fields = [
            "id",
            "report_type",
            "target_type",
            "target_id",
            "target_slug",
            "region_slug",
            "description",
            "reporter_contact",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_description(self, value):
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise serializers.ValidationError(
                "A descrição do relato deve conter pelo menos 10 caracteres."
            )
        if len(cleaned) > 1000:
            raise serializers.ValidationError("A descrição não pode exceder 1000 caracteres.")
        return cleaned

    def validate(self, attrs):
        region_slug = attrs.get("region_slug")
        target_type = attrs.get("target_type")
        target_slug = attrs.get("target_slug")
        target_id = attrs.get("target_id")

        if region_slug:
            if not Region.objects.filter(
                slug=region_slug, status=EditorialStatus.PUBLISHED
            ).exists():
                raise serializers.ValidationError(
                    {"region_slug": f"A região '{region_slug}' não existe ou não está publicada."}
                )

        if target_type == PublicReport.TargetType.ROUTE:
            if not target_slug and not target_id:
                raise serializers.ValidationError(
                    {"target_slug": "É necessário informar o slug ou id da rota."}
                )

            query = Route.objects.filter(editorial_status=EditorialStatus.PUBLISHED)
            if region_slug:
                query = query.filter(region__slug=region_slug)
            if target_id:
                query = query.filter(id=target_id)
            elif target_slug:
                query = query.filter(slug=target_slug)

            if not query.exists():
                msg = "A rota especificada não existe, não está publicada ou não pertence à região."
                raise serializers.ValidationError({"target_slug": msg})

        elif target_type == PublicReport.TargetType.ACTOR:
            if not target_slug and not target_id:
                raise serializers.ValidationError(
                    {"target_slug": "É necessário informar o slug ou id do ponto/ator."}
                )

            query = Actor.objects.filter(
                editorial_status=EditorialStatus.PUBLISHED,
                locations__public_visibility=True,
            )
            if region_slug:
                query = query.filter(locations__region__slug=region_slug)
            if target_id:
                query = query.filter(id=target_id)
            elif target_slug:
                query = query.filter(slug=target_slug)

            if not query.exists():
                msg = "O ponto local não existe, não está publicado ou não pertence à região."
                raise serializers.ValidationError({"target_slug": msg})

        return attrs


class AdminReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicReport
        fields = [
            "id",
            "report_type",
            "target_type",
            "target_id",
            "target_slug",
            "region_slug",
            "description",
            "reporter_contact",
            "status",
            "moderation_note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "report_type",
            "target_type",
            "target_id",
            "target_slug",
            "region_slug",
            "description",
            "reporter_contact",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and getattr(request, "user", None):
            region = resolve_object_region(instance)
            if not has_admin_action(request.user, AdminAction.VIEW_REPORTER_CONTACT, region=region):
                data["reporter_contact"] = ""
        return data


class DashboardSummarySerializer(serializers.Serializer):
    region_slug = serializers.CharField(allow_blank=True)
    priority_reports_count = serializers.IntegerField()
    active_alerts_count = serializers.IntegerField()
    pending_revisions_count = serializers.IntegerField()
