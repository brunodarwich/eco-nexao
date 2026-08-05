from rest_framework.throttling import UserRateThrottle


class AdminReadinessThrottle(UserRateThrottle):
    scope = "admin_readiness"
