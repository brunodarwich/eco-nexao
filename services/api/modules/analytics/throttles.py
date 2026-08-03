from rest_framework.throttling import AnonRateThrottle


class AnalyticsBatchThrottle(AnonRateThrottle):
    scope = "analytics_batch"
