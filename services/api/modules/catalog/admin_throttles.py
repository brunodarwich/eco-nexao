from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle


class GooglePlacesPreviewThrottle(UserRateThrottle):
    scope = "google_places_preview"


class SupportPointCreateUserThrottle(UserRateThrottle):
    scope = "support_point_create_user"


class SupportPointCreateOriginThrottle(SimpleRateThrottle):
    scope = "support_point_create_origin"

    def get_cache_key(self, request, view):
        del view
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
