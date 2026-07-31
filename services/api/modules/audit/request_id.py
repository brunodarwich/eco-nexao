from typing import Any
from uuid import UUID, uuid4


def normalize_request_id(value: Any = None) -> UUID:
    if isinstance(value, UUID):
        return value
    if value:
        try:
            return UUID(str(value))
        except (TypeError, ValueError, AttributeError):
            pass
    return uuid4()


def request_id_from(request: Any) -> UUID:
    return normalize_request_id(getattr(request, "request_id", None))


class RequestIdMiddleware:
    header_name = "HTTP_X_REQUEST_ID"
    response_header = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = normalize_request_id(request.META.get(self.header_name))
        response = self.get_response(request)
        response[self.response_header] = str(request.request_id)
        return response
