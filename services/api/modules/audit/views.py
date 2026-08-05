from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.accounts.permissions import (
    AdminAction,
    AdminRole,
    HasAdminAction,
    get_user_roles,
)

from .models import AuditEvent
from .serializers import AuditEventFilterSerializer, AuditEventSerializer


class AuditEventListView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.VIEW_AUDIT

    @extend_schema(
        operation_id="listAdminAuditEvents",
        tags=["Admin audit"],
        parameters=[AuditEventFilterSerializer],
        responses={
            200: AuditEventSerializer(many=True),
            401: inline_serializer(
                name="AuditError401",
                fields={"detail": serializers.CharField()},
            ),
            403: inline_serializer(
                name="AuditError403",
                fields={"detail": serializers.CharField()},
            ),
        },
    )
    def get(self, request: Request) -> Response:
        filters = AuditEventFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        data = filters.validated_data
        queryset = AuditEvent.objects.select_related("actor", "region")
        if AdminRole.ADMINISTRATOR not in get_user_roles(request.user):
            region_ids = request.user.administrative_region_scopes.filter(
                is_active=True
            ).values_list("region_id", flat=True)
            queryset = queryset.filter(region_id__in=region_ids)
        if action := data.get("action"):
            queryset = queryset.filter(action=action)
        if region_id := data.get("region_id"):
            queryset = queryset.filter(region_id=region_id)
        if target_type := data.get("target_type"):
            queryset = queryset.filter(target_type=target_type)
        if target_id := data.get("target_id"):
            queryset = queryset.filter(target_id=target_id)
        offset = data["offset"]
        events = queryset[offset : offset + data["limit"]]
        return Response(AuditEventSerializer(events, many=True).data)
