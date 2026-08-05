import re
import unicodedata
from collections.abc import Mapping
from urllib.parse import SplitResult, urlsplit, urlunsplit

_WHITESPACE = re.compile(r"\s+")
_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def normalized_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    ascii_text = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return _WHITESPACE.sub(" ", ascii_text).strip()


def normalized_name(value: str) -> str:
    return _NON_ALPHANUMERIC.sub(" ", normalized_text(value)).strip()


def normalized_address(address_fields: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (str(key), normalized_text(str(value)))
            for key, value in address_fields.items()
            if value not in (None, "")
        )
    )


def normalized_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    hostname = parsed.hostname.casefold() if parsed.hostname else ""
    port = f":{parsed.port}" if parsed.port and parsed.port != 443 else ""
    normalized = SplitResult(
        scheme="https",
        netloc=f"{hostname}{port}",
        path=parsed.path or "/",
        query=parsed.query,
        fragment=parsed.fragment,
    )
    return urlunsplit(normalized)


def normalized_contact(channel_type: str, value: str) -> str:
    if channel_type == "email":
        return value.strip().casefold()
    if channel_type in {"website", "instagram"}:
        return normalized_url(value)
    return value.strip()
