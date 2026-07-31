from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.accounts.permissions import AdminAction, HasAdminAction, has_admin_action
from modules.audit.request_id import request_id_from
from modules.routes.models import Route

from .admin_discovery import execute_google_places_preview
from .admin_serializers import (
    ExternalDiscoveryErrorSerializer,
    GooglePlacesPreviewRequestSerializer,
    GooglePlacesPreviewResponseSerializer,
)
from .admin_throttles import GooglePlacesPreviewThrottle
from .google_places import GooglePlacesError


def _error_response(*, code: str, message: str, request: Request, status_code: int) -> Response:
    return Response(
        {
            "code": code,
            "message": message,
            "field_errors": {},
            "request_id": str(request_id_from(request)),
        },
        status=status_code,
    )


class GooglePlacesPreviewView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.DISCOVER_EXTERNAL
    throttle_classes = [GooglePlacesPreviewThrottle]

    @extend_schema(
        operation_id="previewGooglePlacesCandidates",
        tags=["Admin discovery"],
        request=GooglePlacesPreviewRequestSerializer,
        responses={
            200: GooglePlacesPreviewResponseSerializer,
            400: ExternalDiscoveryErrorSerializer,
            403: ExternalDiscoveryErrorSerializer,
            429: ExternalDiscoveryErrorSerializer,
            503: ExternalDiscoveryErrorSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        if not settings.GOOGLE_PLACES_ADMIN_PREVIEW_ENABLED:
            return _error_response(
                code="external_discovery_disabled",
                message="A descoberta externa está desativada neste ambiente.",
                request=request,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = GooglePlacesPreviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        route = get_object_or_404(
            Route.objects.select_related("region"),
            region__slug=data["region_slug"],
            slug=data["route_slug"],
        )
        if not has_admin_action(
            request.user,
            AdminAction.DISCOVER_EXTERNAL,
            region=route.region,
        ):
            raise PermissionDenied("Você não tem acesso à região desta rota.")
        try:
            preview = execute_google_places_preview(
                api_key=settings.GOOGLE_MAPS_API_KEY,
                route=route,
                actor=request.user,
                request_id=request_id_from(request),
                latitude=data["latitude"],
                longitude=data["longitude"],
                radius_meters=data["radius_meters"],
                included_types=data["included_types"],
                max_results=data["max_results"],
            )
        except GooglePlacesError as error:
            return _error_response(
                code="external_provider_unavailable",
                message=str(error),
                request=request,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except (DatabaseError, ValidationError, ValueError):
            return _error_response(
                code="external_discovery_not_recorded",
                message="A consulta não pôde ser registrada com segurança.",
                request=request,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payload = GooglePlacesPreviewResponseSerializer(
            {
                "run_id": preview.recorded.run_id,
                "provider": "google_places",
                "attribution": "Google Maps",
                "result_count": len(preview.candidates),
                "candidates": preview.candidates,
            }
        ).data
        response = Response(payload)
        response["Cache-Control"] = "no-store"
        return response
