from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnalyticsBatchThrottle(AnonRateThrottle):
    scope = "analytics_batch"


class AdminAnalyticsThrottle(UserRateThrottle):
    scope = "admin_analytics"
