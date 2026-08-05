from django.http import JsonResponse


class IntegrationFaultMiddleware:
    """Falha opt-in, disponível somente quando habilitada pelo processo de integração."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.headers.get("X-Integration-Fault") == "database_500":
            return JsonResponse(
                {"code": "integration_database_error", "message": "Falha controlada."},
                status=500,
            )
        return self.get_response(request)

