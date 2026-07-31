import json
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client

from modules.accounts.permissions import AdminAction, AdminRole
from modules.audit.models import AuditEvent


@pytest.fixture
def csrf_client() -> Client:
    return Client(enforce_csrf_checks=True)


@pytest.fixture(autouse=True)
def signed_cookie_sessions(settings) -> None:
    settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
    settings.SESSION_COOKIE_SECURE = False
    settings.CSRF_COOKIE_SECURE = False


@pytest.fixture(autouse=True)
def administrative_identity_lookups(monkeypatch) -> None:
    monkeypatch.setattr(
        "modules.accounts.views.get_user_roles",
        lambda _user: frozenset({AdminRole.EDITOR}),
    )
    monkeypatch.setattr(
        "modules.accounts.views.get_user_actions",
        lambda _user: frozenset({AdminAction.EDIT_CONTENT}),
    )
    monkeypatch.setattr(
        "modules.accounts.views.get_user_region_slugs",
        lambda _user: ("regiao-a",),
    )


@pytest.fixture(autouse=True)
def administrative_audit(monkeypatch) -> None:
    monkeypatch.setattr(
        "modules.accounts.views.record_authentication_event",
        lambda **_kwargs: None,
    )


def _csrf_token(client: Client) -> str:
    response = client.get("/api/v1/admin/auth/csrf")
    assert response.status_code == 200
    return response.json()["csrf_token"]


def _user(*, username: str, is_staff: bool):
    user = get_user_model()(username=username, is_staff=is_staff, is_active=True)
    user.pk = 1
    user.backend = "django.contrib.auth.backends.ModelBackend"
    user.set_password("strong-test-password")
    return user


def test_csrf_bootstrap_sets_separate_cookie(csrf_client: Client) -> None:
    token = _csrf_token(csrf_client)
    cookie = csrf_client.cookies[settings.CSRF_COOKIE_NAME]

    assert token
    assert cookie["httponly"] == ""
    assert cookie["samesite"] == "Lax"
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert settings.SESSION_COOKIE_NAME != settings.CSRF_COOKIE_NAME


def test_login_requires_csrf(csrf_client: Client) -> None:
    response = csrf_client.post(
        "/api/v1/admin/auth/login",
        data=json.dumps({"username": "editor", "password": "secret"}),
        content_type="application/json",
    )

    assert response.status_code == 403
    assert response.json()["code"] == "csrf_failed"


def test_staff_user_can_login_read_session_and_logout(csrf_client: Client) -> None:
    user = _user(username="editor", is_staff=True)
    with patch("modules.accounts.views.record_authentication_event") as record_authentication:
        with (
            patch("modules.accounts.views.authenticate", return_value=user),
            patch.object(user, "save"),
        ):
            login_response = csrf_client.post(
                "/api/v1/admin/auth/login",
                data=json.dumps(
                    {"username": "editor", "password": "strong-test-password"},
                ),
                content_type="application/json",
                headers={"X-CSRFToken": _csrf_token(csrf_client)},
            )

        assert login_response.status_code == 200
        assert login_response.json()["authenticated"] is True
        assert login_response.json()["user"]["username"] == "editor"
        assert login_response.json()["user"]["roles"] == ["editor"]
        assert login_response.json()["user"]["actions"] == ["edit_content"]
        assert login_response.json()["user"]["region_slugs"] == ["regiao-a"]
        assert settings.SESSION_COOKIE_NAME in csrf_client.cookies

        with patch("django.contrib.auth.get_user", return_value=user):
            session_response = csrf_client.get("/api/v1/admin/auth/session")
        assert session_response.status_code == 200
        assert session_response.json()["authenticated"] is True

        with patch("django.contrib.auth.get_user", return_value=user):
            logout_response = csrf_client.post(
                "/api/v1/admin/auth/logout",
                headers={"X-CSRFToken": _csrf_token(csrf_client)},
            )
    assert logout_response.status_code == 200
    assert logout_response.json() == {"authenticated": False, "user": None}
    assert csrf_client.get("/api/v1/admin/auth/session").json()["authenticated"] is False
    assert [call.kwargs["action"] for call in record_authentication.call_args_list] == [
        AuditEvent.Action.AUTH_LOGIN,
        AuditEvent.Action.AUTH_LOGOUT,
    ]


def test_login_rejects_non_staff_and_bad_credentials_with_same_message(
    csrf_client: Client,
) -> None:
    visitor = _user(username="visitor", is_staff=False)
    token = _csrf_token(csrf_client)
    with patch("modules.accounts.views.authenticate", return_value=visitor):
        non_staff = csrf_client.post(
            "/api/v1/admin/auth/login",
            data=json.dumps(
                {"username": "visitor", "password": "strong-test-password"},
            ),
            content_type="application/json",
            headers={"X-CSRFToken": token},
        )
    with patch("modules.accounts.views.authenticate", return_value=None):
        unknown = csrf_client.post(
            "/api/v1/admin/auth/login",
            data=json.dumps({"username": "unknown", "password": "wrong-password"}),
            content_type="application/json",
            headers={"X-CSRFToken": token},
        )

    assert non_staff.status_code == 401
    assert unknown.status_code == 401
    assert non_staff.json()["message"] == unknown.json()["message"]
    assert "visitor" not in non_staff.content.decode()


def test_authenticated_logout_requires_csrf(csrf_client: Client) -> None:
    user = _user(username="editor", is_staff=True)
    with (
        patch("modules.accounts.views.authenticate", return_value=user),
        patch.object(user, "save"),
    ):
        csrf_client.post(
            "/api/v1/admin/auth/login",
            data=json.dumps(
                {"username": "editor", "password": "strong-test-password"},
            ),
            content_type="application/json",
            headers={"X-CSRFToken": _csrf_token(csrf_client)},
        )

    with patch("django.contrib.auth.get_user", return_value=user):
        response = csrf_client.post("/api/v1/admin/auth/logout")
    assert response.status_code == 403
    with patch("django.contrib.auth.get_user", return_value=user):
        session_response = csrf_client.get("/api/v1/admin/auth/session")
    assert session_response.json()["authenticated"] is True
