from django.urls import path

from .admin_views import GooglePlacesPreviewView

urlpatterns = [
    path(
        "google-places/preview",
        GooglePlacesPreviewView.as_view(),
        name="google-places-preview",
    ),
]
