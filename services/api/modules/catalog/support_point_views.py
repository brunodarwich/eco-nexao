import uuid

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.audit.request_id import request_id_from

from .admin_security import SupportPointCreateSecurityMixin
from .support_point_creation import SupportPointCreationConflict, create_support_point
from .support_point_duplicates import DuplicateSupportPointError
from .support_point_serializers import SupportPointCreateRequestSerializer


def _error(request, *, code, message, status_code, candidate_ids=(), field_errors=None):
    payload = {
        "code": code,
        "message": message,
        "field_errors": field_errors or {},
        "request_id": str(request_id_from(request)),
    }
    if candidate_ids:
        payload["duplicate_candidate_ids"] = list(candidate_ids)
    response = Response(payload, status=status_code)
    response["Cache-Control"] = "no-store"
    return response


class SupportPointCreateView(SupportPointCreateSecurityMixin, APIView):
    @extend_schema(exclude=True)
    def post(self, request: Request) -> Response:
        raw_key = request.headers.get("Idempotency-Key", "")
        try:
            key = uuid.UUID(raw_key)
            if key.version != 4:
                raise ValueError
        except (ValueError, AttributeError):
            return _error(
                request,
                code="validation_error",
                message="Idempotency-Key deve ser um UUID v4 válido.",
                status_code=status.HTTP_400_BAD_REQUEST,
                field_errors={"Idempotency-Key": ["Informe um UUID v4 válido."]},
            )

        serializer = SupportPointCreateRequestSerializer(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
        except DuplicateSupportPointError as error:
            return _error(
                request,
                code="duplicate_support_point",
                message=str(error),
                status_code=status.HTTP_409_CONFLICT,
                candidate_ids=error.candidate_ids,
            )
        try:
            result = create_support_point(
                user=request.user,
                data=serializer.validated_data,
                idempotency_key=key,
                request_id=request_id_from(request),
            )
        except DuplicateSupportPointError as error:
            return _error(
                request,
                code="duplicate_support_point",
                message=str(error),
                status_code=status.HTTP_409_CONFLICT,
                candidate_ids=error.candidate_ids,
            )
        except SupportPointCreationConflict as error:
            return _error(
                request,
                code=error.code,
                message=str(error),
                status_code=status.HTTP_409_CONFLICT,
            )
        except Exception:
            return _error(
                request,
                code="internal_error",
                message="O cadastro não pôde ser concluído com segurança.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        response = Response(result.payload, status=status.HTTP_201_CREATED)
        response["Cache-Control"] = "no-store"
        return response
