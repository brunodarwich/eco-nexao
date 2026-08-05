from django.urls import path

from .support_point_views import SupportPointCreateView

urlpatterns = [
    path("support-points/", SupportPointCreateView.as_view(), name="support-point-create"),
]
