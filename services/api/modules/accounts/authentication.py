from rest_framework.authentication import SessionAuthentication


class AdminSessionAuthentication(SessionAuthentication):
    """Session authentication that distinguishes missing identity from forbidden access."""

    def authenticate_header(self, request) -> str:
        del request
        return "Session"
