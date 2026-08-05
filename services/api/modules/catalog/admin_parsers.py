from io import BytesIO

from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser

MAX_SUPPORT_POINT_BODY_BYTES = 64 * 1024
MAX_SUPPORT_POINT_CONTACTS = 10
MAX_SUPPORT_POINT_ROUTE_LINKS = 20


class SupportPointJsonParser(JSONParser):
    """Bound JSON reads even when a proxy omits or falsifies Content-Length."""

    def parse(self, stream, media_type=None, parser_context=None):
        parser_context = parser_context or {}
        request = parser_context.get("request")
        raw_length = getattr(request, "META", {}).get("CONTENT_LENGTH", "")
        try:
            content_length = int(raw_length) if raw_length else None
        except (TypeError, ValueError):
            raise ParseError("O tamanho declarado do corpo é inválido.") from None
        if content_length is not None and content_length > MAX_SUPPORT_POINT_BODY_BYTES:
            raise ParseError("O corpo excede o limite permitido.")

        bounded = stream.read(MAX_SUPPORT_POINT_BODY_BYTES + 1)
        if len(bounded) > MAX_SUPPORT_POINT_BODY_BYTES:
            raise ParseError("O corpo excede o limite permitido.")
        return super().parse(
            BytesIO(bounded),
            media_type=media_type,
            parser_context=parser_context,
        )
