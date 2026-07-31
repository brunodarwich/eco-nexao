from django.urls import path

from .views import CatalogCsvValidationView, CatalogImportCommitView

urlpatterns = [
    path("validate", CatalogCsvValidationView.as_view(), name="catalog-csv-validate"),
    path("commit", CatalogImportCommitView.as_view(), name="catalog-csv-commit"),
]
