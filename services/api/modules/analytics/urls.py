from django.urls import path

from .views import admin_analytics_summary, public_event_batch

urlpatterns = [
    path("events/batch", public_event_batch, name="public_event_batch"),
    path("admin/analytics/summary", admin_analytics_summary, name="admin_analytics_summary"),
]
