from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.accounts.permissions import (
    ROLE_ACTIONS,
    AdminAction,
    AdminRole,
    HasAdminAction,
    actions_for_roles,
    has_admin_action,
    role_group_name,
)


class FakeGroups:
    def __init__(self, roles: set[AdminRole]):
        self.names = [role_group_name(role) for role in roles]

    def values_list(self, _field: str, *, flat: bool):
        assert flat is True
        return self.names


class FakeScopes:
    def __init__(self, region_ids: set[str]):
        self.region_ids = region_ids
        self.filters: dict[str, object] = {}

    def filter(self, **kwargs):
        self.filters = kwargs
        return self

    def exists(self) -> bool:
        return (
            self.filters.get("is_active") is True
            and self.filters.get("region_id") in self.region_ids
        )


def fake_user(
    *roles: AdminRole,
    region_ids: set[str] | None = None,
    is_staff: bool = True,
    is_superuser: bool = False,
):
    return SimpleNamespace(
        administrative_region_scopes=FakeScopes(region_ids or set()),
        groups=FakeGroups(set(roles)),
        is_active=True,
        is_authenticated=True,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )


EXPECTED_ACTIONS = {
    AdminRole.EDITOR: {
        AdminAction.EDIT_CONTENT,
        AdminAction.IMPORT_CSV,
        AdminAction.VIEW_AGGREGATES,
        AdminAction.DISCOVER_EXTERNAL,
        AdminAction.LIST_REPORTS,
    },
    AdminRole.REVIEWER: {
        AdminAction.EDIT_CONTENT,
        AdminAction.IMPORT_CSV,
        AdminAction.APPROVE,
        AdminAction.VIEW_AGGREGATES,
        AdminAction.VIEW_AUDIT,
        AdminAction.DISCOVER_EXTERNAL,
        AdminAction.LIST_REPORTS,
        AdminAction.MODERATE_REPORT,
        AdminAction.VIEW_REPORTER_CONTACT,
    },
    AdminRole.PUBLISHER: {
        AdminAction.EDIT_CONTENT,
        AdminAction.IMPORT_CSV,
        AdminAction.APPROVE,
        AdminAction.PUBLISH,
        AdminAction.VIEW_AGGREGATES,
        AdminAction.VIEW_AUDIT,
        AdminAction.LIST_REPORTS,
        AdminAction.MODERATE_REPORT,
        AdminAction.VIEW_REPORTER_CONTACT,
        AdminAction.VIEW_ANALYTICS,
    },
    AdminRole.ANALYST: {
        AdminAction.VIEW_AGGREGATES,
        AdminAction.VIEW_ANALYTICS,
    },
    AdminRole.ADMINISTRATOR: set(AdminAction),
}


@pytest.mark.parametrize(("role", "expected"), EXPECTED_ACTIONS.items())
def test_role_action_matrix_matches_product_spec(role, expected):
    assert ROLE_ACTIONS[role] == expected


def test_multiple_roles_combine_actions_without_implicit_hierarchy():
    actions = actions_for_roles({AdminRole.EDITOR, AdminRole.ANALYST})

    assert AdminAction.EDIT_CONTENT in actions
    assert AdminAction.VIEW_AGGREGATES in actions
    assert AdminAction.APPROVE not in actions
    assert AdminAction.PUBLISH not in actions


def test_region_scopes_limit_object_actions():
    editor = fake_user(AdminRole.EDITOR, region_ids={"region-a"})

    assert has_admin_action(
        editor,
        AdminAction.EDIT_CONTENT,
        region=SimpleNamespace(pk="region-a"),
    )
    assert not has_admin_action(
        editor,
        AdminAction.EDIT_CONTENT,
        region=SimpleNamespace(pk="region-b"),
    )


def test_attempts_to_escalate_role_or_scope_are_denied():
    editor = fake_user(
        AdminRole.EDITOR,
        region_ids={"region-a"},
        is_superuser=True,
    )
    publisher = fake_user(AdminRole.PUBLISHER, region_ids={"region-a"})

    assert not has_admin_action(editor, AdminAction.PUBLISH, region="region-a")
    assert not has_admin_action(editor, AdminAction.MANAGE_USERS)
    assert not has_admin_action(publisher, AdminAction.PUBLISH, region="region-b")


def test_administrator_has_global_scope_but_non_staff_never_enters_admin():
    administrator = fake_user(AdminRole.ADMINISTRATOR)
    non_staff = fake_user(AdminRole.ADMINISTRATOR, is_staff=False)

    assert has_admin_action(administrator, AdminAction.MANAGE_USERS)
    assert has_admin_action(administrator, AdminAction.PUBLISH, region="any-region")
    assert not has_admin_action(non_staff, AdminAction.MANAGE_USERS)


def test_drf_permission_fails_closed_without_declared_action():
    permission = HasAdminAction()
    request = SimpleNamespace(user=fake_user(AdminRole.ADMINISTRATOR))

    assert permission.has_permission(request, SimpleNamespace()) is False

    view = SimpleNamespace(required_admin_action="publish")
    assert permission.has_permission(request, view) is False


def test_drf_permission_uses_server_resolved_region():
    permission = HasAdminAction()
    user = fake_user(AdminRole.EDITOR, region_ids={"region-a"})
    request = SimpleNamespace(user=user)
    resolver = MagicMock(return_value=SimpleNamespace(pk="region-a"))
    view = SimpleNamespace(
        required_admin_action=AdminAction.EDIT_CONTENT,
        get_permission_region=resolver,
    )

    assert permission.has_permission(request, view) is True
    resolver.assert_called_once_with(request)
