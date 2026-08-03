from django.urls import path

from . import views

urlpatterns = [
    path("public/reports/", views.public_create_report, name="public_create_report"),
    path("admin/reports/", views.admin_list_reports, name="admin_list_reports"),
    path(
        "admin/reports/<uuid:report_id>/",
        views.admin_moderate_report,
        name="admin_moderate_report",
    ),
]
