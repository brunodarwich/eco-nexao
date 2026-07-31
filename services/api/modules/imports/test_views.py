from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from drf_spectacular.generators import SchemaGenerator

from modules.accounts.permissions import AdminAction

from .catalog_csv import CatalogCsvValidationResult, ValidationIssue
from .commit import CatalogImportCommitResult
from .throttles import CatalogCsvValidationThrottle
from .views import CatalogCsvValidationView, CatalogImportCommitView


def test_validation_endpoint_is_ephemeral_protected_and_rate_limited():
    upload = SimpleUploadedFile("catalog.csv", b"content", content_type="text/csv")
    request = SimpleNamespace(data={"file": upload}, user=SimpleNamespace(pk=1))
    result = CatalogCsvValidationResult(
        sha256="a" * 64,
        row_count=3,
        issues=(),
    )

    with (
        patch(
            "modules.imports.views.catalog_relation_index_for",
            return_value=SimpleNamespace(),
        ),
        patch("modules.imports.views.validate_catalog_csv", return_value=result) as validate,
    ):
        response = CatalogCsvValidationView().post(request)

    assert response.data == {
        "valid": True,
        "sha256": "a" * 64,
        "row_count": 3,
        "error_count": 0,
        "warning_count": 0,
        "issues_truncated": False,
        "issues": [],
        "preview": {
            "create_count": 0,
            "update_count": 0,
            "archive_count": 0,
            "rows": [],
        },
    }
    assert response["Cache-Control"] == "no-store"
    assert validate.call_args.args[0] == b"content"
    assert CatalogCsvValidationView.required_admin_action == AdminAction.IMPORT_CSV
    assert CatalogCsvValidationView.throttle_classes == [CatalogCsvValidationThrottle]


def test_openapi_documents_multipart_validation_contract():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/admin/imports/validate"]["post"]

    assert "multipart/form-data" in operation["requestBody"]["content"]
    assert operation["security"]
    assert operation["operationId"] == "validateCatalogCsv"
    commit = schema["paths"]["/api/v1/admin/imports/commit"]["post"]
    assert "multipart/form-data" in commit["requestBody"]["content"]
    assert commit["security"]
    assert commit["operationId"] == "commitCatalogCsv"


def test_validation_endpoint_returns_actionable_issue_report_without_preview():
    upload = SimpleUploadedFile("catalog.csv", b"content", content_type="text/csv")
    request = SimpleNamespace(data={"file": upload}, user=SimpleNamespace(pk=1))
    result = CatalogCsvValidationResult(
        sha256="b" * 64,
        row_count=1,
        issues=(
            ValidationIssue(
                severity="error",
                code="required",
                line=2,
                column="public_name",
                message="Campo obrigatório não informado.",
            ),
        ),
    )

    with (
        patch(
            "modules.imports.views.catalog_relation_index_for",
            return_value=SimpleNamespace(),
        ),
        patch("modules.imports.views.validate_catalog_csv", return_value=result),
    ):
        response = CatalogCsvValidationView().post(request)

    assert response.data["valid"] is False
    assert response.data["preview"] is None
    assert response.data["issues"] == [
        {
            "severity": "error",
            "code": "required",
            "line": 2,
            "column": "public_name",
            "message": "Campo obrigatório não informado.",
        }
    ]


def test_commit_endpoint_requires_confirmation_and_returns_no_store_result():
    upload = SimpleUploadedFile("catalog.csv", b"content", content_type="text/csv")
    request = SimpleNamespace(
        data={
            "file": upload,
            "sha256": "a" * 64,
            "idempotency_key": str(uuid4()),
            "confirmed": True,
        },
        user=SimpleNamespace(pk=1),
        META={},
        headers={},
    )
    batch = SimpleNamespace(
        pk=uuid4(),
        status="committed",
        sha256="a" * 64,
        row_count=2,
        warning_count=1,
        create_count=1,
        update_count=1,
        archive_count=0,
        committed_at="2026-07-29T20:00:00-03:00",
    )

    with (
        patch(
            "modules.imports.views.catalog_relation_index_for",
            return_value=SimpleNamespace(),
        ),
        patch(
            "modules.imports.views.commit_catalog_import",
            return_value=CatalogImportCommitResult(batch, replayed=False),
        ) as commit,
    ):
        response = CatalogImportCommitView().post(request)

    assert response.status_code == 201
    assert response.data["replayed"] is False
    assert response.data["create_count"] == 1
    assert response["Cache-Control"] == "no-store"
    assert CatalogImportCommitView.required_admin_action == AdminAction.IMPORT_CSV
    assert CatalogImportCommitView.throttle_classes == [CatalogCsvValidationThrottle]
    assert commit.call_args.kwargs["content"] == b"content"
