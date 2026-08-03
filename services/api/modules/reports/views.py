from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from modules.accounts.permissions import (
    AdminAction,
    AdminRole,
    get_user_region_slugs,
    get_user_roles,
    has_admin_action,
    resolve_object_region,
)
from modules.audit.models import AuditEvent
from modules.audit.service import record_audit_event

from .models import PublicReport
from .serializers import AdminReportSerializer, PublicReportCreateSerializer
from .throttles import PublicReportCreateThrottle


class PublicReportCreatedResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    message = serializers.CharField()
    status = serializers.CharField()


@extend_schema(
    request=PublicReportCreateSerializer,
    responses={
        201: PublicReportCreatedResponseSerializer,
        400: {"type": "object", "additionalProperties": True},
        429: {"type": "object", "properties": {"detail": {"type": "string"}}},
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicReportCreateThrottle])
def public_create_report(request):
    """
    Criação pública de relato de informação incorreta.
    Protegido contra autopublicação e abusos de tamanho.
    """
    serializer = PublicReportCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    report = serializer.save()
    return Response(
        {
            "id": str(report.id),
            "message": "Seu relato foi recebido e enviado para revisão editorial.",
            "status": report.status,
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    responses={
        200: AdminReportSerializer(many=True),
        401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        403: {"type": "object", "properties": {"detail": {"type": "string"}}},
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_list_reports(request):
    """
    Lista relatos da comunidade para moderação e triagem.
    """
    if not has_admin_action(request.user, AdminAction.LIST_REPORTS):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)

    reports = PublicReport.objects.all()

    roles = get_user_roles(request.user)
    if AdminRole.ADMINISTRATOR not in roles:
        allowed_slugs = get_user_region_slugs(request.user)
        reports = reports.filter(region_slug__in=allowed_slugs)

    status_filter = request.query_params.get("status")
    region_filter = request.query_params.get("region_slug")
    if status_filter:
        reports = reports.filter(status=status_filter)
    if region_filter:
        reports = reports.filter(region_slug=region_filter)

    serializer = AdminReportSerializer(reports, many=True, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=AdminReportSerializer,
    responses={
        200: AdminReportSerializer,
        400: {"type": "object", "additionalProperties": True},
        401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        403: {"type": "object", "properties": {"detail": {"type": "string"}}},
        404: {"type": "object", "properties": {"detail": {"type": "string"}}},
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def admin_moderate_report(request, report_id):
    """
    Atualiza o status de moderação e nota técnica de um relato.
    """
    try:
        report = PublicReport.objects.get(id=report_id)
    except PublicReport.DoesNotExist:
        return Response(
            {"detail": "Relato não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    report_region = resolve_object_region(report)
    if not has_admin_action(request.user, AdminAction.MODERATE_REPORT, region=report_region):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)

    serializer = AdminReportSerializer(
        report, data=request.data, partial=True, context={"request": request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    previous_status = report.status
    with transaction.atomic():
        updated_report = serializer.save()
        if request.user and request.user.is_authenticated:
            record_audit_event(
                actor=request.user,
                action=AuditEvent.Action.REPORT_MODERATE,
                target_type="PublicReport",
                target_id=str(updated_report.id),
                request_id=getattr(request, "request_id", None),
                reason=f"Status alterado para {updated_report.status}",
                metadata={
                    "report_id": str(updated_report.id),
                    "previous_status": previous_status,
                    "new_status": updated_report.status,
                },
            )
    return Response(
        AdminReportSerializer(updated_report, context={"request": request}).data,
        status=status.HTTP_200_OK,
    )
