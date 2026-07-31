from rest_framework.throttling import UserRateThrottle


class GooglePlacesPreviewThrottle(UserRateThrottle):
    scope = "google_places_preview"
