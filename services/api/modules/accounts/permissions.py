from collections.abc import Iterable
from enum import StrEnum
from typing import Any

from rest_framework.permissions import BasePermission


class AdminRole(StrEnum):
    EDITOR = "editor"
    REVIEWER = "reviewer"
    PUBLISHER = "publisher"
    ANALYST = "analyst"
    ADMINISTRATOR = "administrator"


class AdminAction(StrEnum):
    EDIT_CONTENT = "edit_content"
    IMPORT_CSV = "import_csv"
    APPROVE = "approve"
    PUBLISH = "publish"
    VIEW_AGGREGATES = "view_aggregates"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT = "view_audit"
    DISCOVER_EXTERNAL = "discover_external"


ROLE_GROUP_PREFIX = "econexao:"

ROLE_ACTIONS: dict[AdminRole, frozenset[AdminAction]] = {
    AdminRole.EDITOR: frozenset(
        {
            AdminAction.EDIT_CONTENT,
            AdminAction.IMPORT_CSV,
            AdminAction.VIEW_AGGREGATES,
            AdminAction.DISCOVER_EXTERNAL,
        }
    ),
    AdminRole.REVIEWER: frozenset(
        {
            AdminAction.EDIT_CONTENT,
            AdminAction.IMPORT_CSV,
            AdminAction.APPROVE,
            AdminAction.VIEW_AGGREGATES,
            AdminAction.VIEW_AUDIT,
            AdminAction.DISCOVER_EXTERNAL,
        }
    ),
    AdminRole.PUBLISHER: frozenset(
        {
            AdminAction.EDIT_CONTENT,
            AdminAction.IMPORT_CSV,
            AdminAction.APPROVE,
            AdminAction.PUBLISH,
            AdminAction.VIEW_AGGREGATES,
            AdminAction.VIEW_AUDIT,
        }
    ),
    AdminRole.ANALYST: frozenset({AdminAction.VIEW_AGGREGATES}),
    AdminRole.ADMINISTRATOR: frozenset(AdminAction),
}


def role_group_name(role: AdminRole) -> str:
    return f"{ROLE_GROUP_PREFIX}{role.value}"


def actions_for_roles(roles: Iterable[AdminRole]) -> frozenset[AdminAction]:
    return frozenset(action for role in roles for action in ROLE_ACTIONS[role])


def get_user_roles(user: Any) -> frozenset[AdminRole]:
    if not getattr(user, "is_authenticated", False):
        return frozenset()
    group_names = user.groups.values_list("name", flat=True)
    valid_groups = {role_group_name(role): role for role in AdminRole}
    return frozenset(
        valid_groups[group_name] for group_name in group_names if group_name in valid_groups
    )


def get_user_actions(user: Any) -> frozenset[AdminAction]:
    return actions_for_roles(get_user_roles(user))


def get_user_region_slugs(user: Any) -> tuple[str, ...]:
    if not getattr(user, "is_authenticated", False):
        return ()
    return tuple(
        user.administrative_region_scopes.filter(is_active=True)
        .order_by("region__slug")
        .values_list("region__slug", flat=True)
    )


def has_admin_action(user: Any, action: AdminAction, *, region: Any | None = None) -> bool:
    if not (
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "is_staff", False)
    ):
        return False

    roles = get_user_roles(user)
    if action not in actions_for_roles(roles):
        return False
    if AdminRole.ADMINISTRATOR in roles or region is None:
        return True

    region_id = getattr(region, "pk", region)
    return user.administrative_region_scopes.filter(
        region_id=region_id,
        is_active=True,
    ).exists()


def resolve_object_region(instance: Any) -> Any | None:
    region = getattr(instance, "region", None)
    if region is not None:
        return region
    route = getattr(instance, "route", None)
    if route is not None:
        return getattr(route, "region", None)
    return None


class HasAdminAction(BasePermission):
    message = "Você não tem permissão para executar esta ação."

    def has_permission(self, request, view) -> bool:
        action = getattr(view, "required_admin_action", None)
        if not isinstance(action, AdminAction):
            return False
        region_resolver = getattr(view, "get_permission_region", None)
        region = region_resolver(request) if callable(region_resolver) else None
        return has_admin_action(request.user, action, region=region)

    def has_object_permission(self, request, view, obj) -> bool:
        action = getattr(view, "required_admin_action", None)
        if not isinstance(action, AdminAction):
            return False
        return has_admin_action(
            request.user,
            action,
            region=resolve_object_region(obj),
        )
