from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/v1/", include("modules.health.urls")),
    path("api/v1/", include("modules.regions.urls")),
    path("api/v1/", include("modules.routes.urls")),
    path("api/v1/admin/auth/", include("modules.accounts.urls")),
    path("api/v1/admin/", include("modules.audit.urls")),
    path("api/v1/admin/discovery/", include("modules.catalog.admin_urls")),
    path("api/v1/admin/imports/", include("modules.imports.urls")),
    path("api/v1/admin/editorial/", include("modules.publishing.urls")),
    path("api/v1/", include("modules.reports.urls")),
    path("api/v1/", include("modules.analytics.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
