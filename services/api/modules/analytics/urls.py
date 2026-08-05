from django.urls import path

from .views import admin_analytics_summary, admin_operational_analytics, public_event_batch

urlpatterns = [
    path("events/batch", public_event_batch, name="public_event_batch"),
    path("admin/analytics/summary", admin_analytics_summary, name="admin_analytics_summary"),
    path(
        "admin/analytics/operational",
        admin_operational_analytics,
        name="admin_operational_analytics",
    ),
]
