from django.db import transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema
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
from modules.publishing.models import EditorialRevision

from .models import PublicReport
from .serializers import (
    AdminReportSerializer,
    DashboardSummarySerializer,
    PublicReportCreateSerializer,
)
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


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="region_slug",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Slug da região para filtrar os contadores operacionais.",
            required=False,
        )
    ],
    responses={
        200: DashboardSummarySerializer,
        401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        403: {"type": "object", "properties": {"detail": {"type": "string"}}},
        429: {"type": "object", "properties": {"detail": {"type": "string"}}},
        500: {"type": "object", "properties": {"detail": {"type": "string"}}},
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard_summary(request):
    """
    Retorna contadores operacionais consolidados sem dados pessoais (PII) por região.
    """
    if not (
        has_admin_action(request.user, AdminAction.VIEW_AGGREGATES)
        or has_admin_action(request.user, AdminAction.LIST_REPORTS)
        or has_admin_action(request.user, AdminAction.VIEW_ANALYTICS)
    ):
        return Response({"detail": "Permissão negada."}, status=status.HTTP_403_FORBIDDEN)

    roles = get_user_roles(request.user)
    allowed_region_slugs = None
    if AdminRole.ADMINISTRATOR not in roles:
        allowed_region_slugs = set(get_user_region_slugs(request.user))

    region_slug = request.query_params.get("region_slug")
    if region_slug:
        if allowed_region_slugs is not None and region_slug not in allowed_region_slugs:
            return Response(
                {"detail": "Você não tem permissão para acessar esta região."},
                status=status.HTTP_403_FORBIDDEN,
            )

    reports_qs = PublicReport.objects.filter(status=PublicReport.Status.PENDING)
    revisions_qs = EditorialRevision.objects.filter(status=EditorialRevision.Status.REVIEW)

    if region_slug:
        reports_qs = reports_qs.filter(region_slug=region_slug)
        revisions_qs = revisions_qs.filter(region__slug=region_slug)
    elif allowed_region_slugs is not None:
        reports_qs = reports_qs.filter(region_slug__in=allowed_region_slugs)
        revisions_qs = revisions_qs.filter(region__slug__in=allowed_region_slugs)

    active_alerts_count = reports_qs.filter(
        report_type=PublicReport.ReportType.SAFETY_WARNING
    ).count()
    priority_reports_count = reports_qs.filter(
        report_type__in=[
            PublicReport.ReportType.SAFETY_WARNING,
            PublicReport.ReportType.CLOSED_LOCATION,
        ]
    ).count()
    pending_revisions_count = revisions_qs.count()

    serializer = DashboardSummarySerializer(
        {
            "region_slug": region_slug or "",
            "priority_reports_count": priority_reports_count,
            "active_alerts_count": active_alerts_count,
            "pending_revisions_count": pending_revisions_count,
        }
    )
    return Response(serializer.data, status=status.HTTP_200_OK)
