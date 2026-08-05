import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.middleware.csrf import get_token
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from modules.accounts.authentication import AdminSessionAuthentication
from modules.accounts.permissions import AdminAction, HasAdminAction

from .admin_parsers import (
    MAX_SUPPORT_POINT_BODY_BYTES,
    MAX_SUPPORT_POINT_CONTACTS,
    MAX_SUPPORT_POINT_ROUTE_LINKS,
    SupportPointJsonParser,
)
from .admin_permissions import require_support_point_region_access
from .admin_security import SupportPointCreateSecurityMixin
from .admin_throttles import (
    SupportPointCreateOriginThrottle,
    SupportPointCreateUserThrottle,
)


class ProtectedProbeView(APIView):
    authentication_classes = [AdminSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):  # pragma: no cover - authentication stops first
        raise AssertionError(f"Probe should not execute for {request.user!r}")


class OneRequestUserThrottle(SupportPointCreateUserThrottle):
    def get_rate(self):
        return "1/hour"


class OneRequestOriginThrottle(SupportPointCreateOriginThrottle):
    def get_rate(self):
        return "1/hour"


class ThrottledProbeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [OneRequestUserThrottle, OneRequestOriginThrottle]

    def post(self, request):
        return Response(status=204)


def _configure_one_request(throttle):
    throttle.rate = "1/hour"
    throttle.num_requests, throttle.duration = throttle.parse_rate(throttle.rate)
    return throttle


def test_missing_session_uses_401_instead_of_conflating_with_forbidden():
    request = APIRequestFactory().post("/probe", {}, format="json")
    request.user = AnonymousUser()

    response = ProtectedProbeView.as_view()(request)

    assert response.status_code == 401
    assert response["WWW-Authenticate"] == "Session"


def test_session_authentication_rejects_missing_csrf_and_accepts_matching_token():
    factory = APIRequestFactory(enforce_csrf_checks=True)
    authentication = AdminSessionAuthentication()
    missing = factory.post("/probe", {}, format="json")

    with pytest.raises(PermissionDenied):
        authentication.enforce_csrf(missing)

    accepted = factory.post("/probe", {}, format="json")
    token = get_token(accepted)
    accepted.COOKIES[settings.CSRF_COOKIE_NAME] = accepted.META["CSRF_COOKIE"]
    accepted.META["HTTP_X_CSRFTOKEN"] = token

    authentication.enforce_csrf(accepted)


def test_region_access_uses_server_resolved_region_and_fails_closed():
    user = SimpleNamespace(pk=1)
    allowed_region = SimpleNamespace(pk="region-a")
    denied_region = SimpleNamespace(pk="region-b")

    with patch(
        "modules.catalog.admin_permissions.has_admin_action",
        side_effect=lambda _user, _action, *, region: region.pk == "region-a",
    ):
        require_support_point_region_access(user, allowed_region)
        with pytest.raises(PermissionDenied):
            require_support_point_region_access(user, denied_region)


def test_user_and_origin_throttles_are_independent_and_return_wait_time():
    cache.clear()
    view = SimpleNamespace()
    first_user_request = SimpleNamespace(
        user=SimpleNamespace(pk=1, is_authenticated=True),
        META={"REMOTE_ADDR": "192.0.2.10"},
    )
    second_user_request = SimpleNamespace(
        user=SimpleNamespace(pk=2, is_authenticated=True),
        META={"REMOTE_ADDR": "192.0.2.10"},
    )

    user_throttle = _configure_one_request(SupportPointCreateUserThrottle())
    assert user_throttle.allow_request(first_user_request, view) is True
    assert user_throttle.allow_request(first_user_request, view) is False
    assert user_throttle.wait() > 0

    origin_throttle = _configure_one_request(SupportPointCreateOriginThrottle())
    assert origin_throttle.allow_request(first_user_request, view) is True
    assert origin_throttle.allow_request(second_user_request, view) is False
    assert origin_throttle.wait() > 0


def test_throttle_pipeline_returns_429_with_retry_after():
    cache.clear()
    factory = APIRequestFactory()
    user = SimpleNamespace(pk=99, is_authenticated=True, is_active=True)

    first = factory.post("/probe", {}, format="json", REMOTE_ADDR="192.0.2.99")
    force_authenticate(first, user=user)
    assert ThrottledProbeView.as_view()(first).status_code == 204

    repeated = factory.post("/probe", {}, format="json", REMOTE_ADDR="192.0.2.99")
    force_authenticate(repeated, user=user)
    response = ThrottledProbeView.as_view()(repeated)

    assert response.status_code == 429
    assert int(response["Retry-After"]) >= 1


def test_support_point_parser_enforces_declared_and_actual_body_limit():
    parser = SupportPointJsonParser()
    small_payload = json.dumps({"actor": {"public_name": "Apoio"}}).encode()
    request = SimpleNamespace(META={"CONTENT_LENGTH": str(len(small_payload))})

    assert parser.parse(BytesIO(small_payload), parser_context={"request": request}) == {
        "actor": {"public_name": "Apoio"}
    }

    declared_oversize = SimpleNamespace(
        META={"CONTENT_LENGTH": str(MAX_SUPPORT_POINT_BODY_BYTES + 1)}
    )
    with pytest.raises(ParseError, match="excede"):
        parser.parse(BytesIO(b"{}"), parser_context={"request": declared_oversize})

    no_declared_length = SimpleNamespace(META={})
    with pytest.raises(ParseError, match="excede"):
        parser.parse(
            BytesIO(b" " * (MAX_SUPPORT_POINT_BODY_BYTES + 1)),
            parser_context={"request": no_declared_length},
        )


def test_cardinality_limits_match_the_approved_contract():
    assert MAX_SUPPORT_POINT_CONTACTS == 10
    assert MAX_SUPPORT_POINT_ROUTE_LINKS == 20
    assert SupportPointCreateUserThrottle.scope == "support_point_create_user"
    assert SupportPointCreateOriginThrottle.scope == "support_point_create_origin"


def test_future_view_security_policy_cannot_omit_any_approved_layer():
    assert SupportPointCreateSecurityMixin.authentication_classes == [AdminSessionAuthentication]
    assert SupportPointCreateSecurityMixin.permission_classes == [HasAdminAction]
    assert SupportPointCreateSecurityMixin.required_admin_action == AdminAction.CREATE_SUPPORT_POINT
    assert SupportPointCreateSecurityMixin.parser_classes == [SupportPointJsonParser]
    assert SupportPointCreateSecurityMixin.throttle_classes == [
        SupportPointCreateUserThrottle,
        SupportPointCreateOriginThrottle,
    ]
