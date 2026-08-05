from typing import Any

from rest_framework.exceptions import PermissionDenied

from modules.accounts.permissions import AdminAction, has_admin_action


def require_support_point_region_access(user: Any, region: Any) -> None:
    """Fail closed after the server has resolved the region from route relations."""
    if not has_admin_action(user, AdminAction.CREATE_SUPPORT_POINT, region=region):
        raise PermissionDenied("Você não tem permissão para cadastrar pontos nesta região.")
