from django.urls import path

from .views import AuditEventListView

urlpatterns = [
    path("audit-logs", AuditEventListView.as_view(), name="admin-audit-event-list"),
]
