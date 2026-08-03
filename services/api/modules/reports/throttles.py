from rest_framework.throttling import AnonRateThrottle


class PublicReportCreateThrottle(AnonRateThrottle):
    scope = "public_reports"
