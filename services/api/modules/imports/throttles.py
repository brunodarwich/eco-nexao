from rest_framework.throttling import UserRateThrottle


class CatalogCsvValidationThrottle(UserRateThrottle):
    scope = "csv_validation"
