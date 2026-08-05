from rest_framework.exceptions import APIException, Throttled

from modules.accounts.authentication import AdminSessionAuthentication
from modules.accounts.permissions import AdminAction, HasAdminAction
from modules.audit.request_id import request_id_from

from .admin_parsers import SupportPointJsonParser
from .admin_throttles import (
    SupportPointCreateOriginThrottle,
    SupportPointCreateUserThrottle,
)


class SupportPointCreateSecurityMixin:
    """Mandatory security policy for the future support-point creation view."""

    authentication_classes = [AdminSessionAuthentication]
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.CREATE_SUPPORT_POINT
    throttle_classes = [
        SupportPointCreateUserThrottle,
        SupportPointCreateOriginThrottle,
    ]
    parser_classes = [SupportPointJsonParser]

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if isinstance(exc, APIException):
            detail = exc.detail
            field_errors = detail if isinstance(detail, dict) else {}
            message = "A requisição administrativa não pôde ser processada."
            if not field_errors:
                message = str(detail)
            code = getattr(exc, "default_code", "request_failed")
            code = {
                "not_authenticated": "authentication_required",
                "authentication_failed": "authentication_required",
                "throttled": "rate_limited",
                "parse_error": "validation_error",
            }.get(code, code)
            response.data = {
                "code": code,
                "message": message,
                "field_errors": field_errors,
                "request_id": str(request_id_from(self.request)),
            }
            response["Cache-Control"] = "no-store"
            if isinstance(exc, Throttled):
                response["Retry-After"] = str(max(1, int(exc.wait or 1)))
        return response
