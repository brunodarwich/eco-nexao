from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.audit.models import AuditEvent
from modules.audit.request_id import request_id_from
from modules.audit.service import record_authentication_event

from .permissions import get_user_actions, get_user_region_slugs, get_user_roles
from .serializers import (
    CsrfResponseSerializer,
    LoginRequestSerializer,
    SessionResponseSerializer,
)


def _identity(user) -> dict[str, object]:
    return {
        "id": str(user.pk),
        "username": user.get_username(),
        "roles": sorted(role.value for role in get_user_roles(user)),
        "actions": sorted(action.value for action in get_user_actions(user)),
        "region_slugs": list(get_user_region_slugs(user)),
    }


def _session_payload(user) -> dict[str, object]:
    if user.is_authenticated and user.is_active and user.is_staff:
        return {"authenticated": True, "user": _identity(user)}
    return {"authenticated": False, "user": None}


def _error(*, code: str, message: str, request=None) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "field_errors": {},
        "request_id": str(request_id_from(request)),
    }


def csrf_failure(request, reason="") -> JsonResponse:
    return JsonResponse(
        _error(
            code="csrf_failed",
            message="A validação de segurança da sessão falhou.",
            request=request,
        ),
        status=status.HTTP_403_FORBIDDEN,
    )


@method_decorator(never_cache, name="dispatch")
@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="getAdminCsrfToken",
        tags=["Admin auth"],
        responses={200: CsrfResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response({"csrf_token": get_token(request)})


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="loginAdmin",
        tags=["Admin auth"],
        request=LoginRequestSerializer,
        responses={
            200: SessionResponseSerializer,
            401: inline_serializer(
                name="LoginError401",
                fields={
                    "code": serializers.CharField(),
                    "message": serializers.CharField(),
                    "field_errors": serializers.DictField(),
                    "request_id": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    **_error(
                        code="invalid_credentials",
                        message="Usuário ou senha inválidos.",
                        request=request,
                    ),
                    "field_errors": {
                        field: [str(message) for message in messages]
                        for field, messages in serializer.errors.items()
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None or not user.is_active or not user.is_staff:
            return Response(
                _error(
                    code="invalid_credentials",
                    message="Usuário ou senha inválidos.",
                    request=request,
                ),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        record_authentication_event(
            actor=user,
            action=AuditEvent.Action.AUTH_LOGIN,
            request_id=request_id_from(request),
        )
        return Response(_session_payload(user))


@method_decorator(never_cache, name="dispatch")
class SessionView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="getAdminSession",
        tags=["Admin auth"],
        responses={200: SessionResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(_session_payload(request.user))


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="logoutAdmin",
        tags=["Admin auth"],
        request=None,
        responses={200: SessionResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        user = request.user
        logout(request)
        if user.is_authenticated and user.is_active and user.is_staff:
            record_authentication_event(
                actor=user,
                action=AuditEvent.Action.AUTH_LOGOUT,
                request_id=request_id_from(request),
            )
        return Response({"authenticated": False, "user": None})
