from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.accounts.permissions import AdminAction, HasAdminAction
from modules.audit.request_id import request_id_from

from .catalog_csv import MAX_CSV_BYTES, validate_catalog_csv
from .commit import CatalogImportCommitError, commit_catalog_import
from .relations import catalog_relation_index_for
from .serializers import (
    CatalogCsvCommitRequestSerializer,
    CatalogCsvValidationRequestSerializer,
    CatalogCsvValidationResponseSerializer,
    CatalogImportCommitErrorSerializer,
    CatalogImportCommitResponseSerializer,
)
from .throttles import CatalogCsvValidationThrottle


class CatalogCsvValidationView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.IMPORT_CSV
    throttle_classes = [CatalogCsvValidationThrottle]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        operation_id="validateCatalogCsv",
        tags=["Admin imports"],
        request=CatalogCsvValidationRequestSerializer,
        responses={200: CatalogCsvValidationResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = CatalogCsvValidationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]
        content = upload.read(MAX_CSV_BYTES + 1)
        result = validate_catalog_csv(content, catalog_relation_index_for(request.user))
        operations = [row.operation for row in result.preview_rows]
        preview = None
        if result.valid:
            preview = {
                "create_count": operations.count("create"),
                "update_count": operations.count("update"),
                "archive_count": operations.count("archive"),
                "rows": result.preview_rows,
            }
        payload = CatalogCsvValidationResponseSerializer(
            {
                "valid": result.valid,
                "sha256": result.sha256,
                "row_count": result.row_count,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "issues_truncated": result.issues_truncated,
                "issues": result.issues,
                "preview": preview,
            }
        ).data
        response = Response(payload)
        response["Cache-Control"] = "no-store"
        return response


class CatalogImportCommitView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.IMPORT_CSV
    throttle_classes = [CatalogCsvValidationThrottle]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        operation_id="commitCatalogCsv",
        tags=["Admin imports"],
        request=CatalogCsvCommitRequestSerializer,
        responses={
            200: CatalogImportCommitResponseSerializer,
            201: CatalogImportCommitResponseSerializer,
            400: CatalogImportCommitErrorSerializer,
            409: CatalogImportCommitErrorSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = CatalogCsvCommitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        upload = data["file"]
        content = upload.read(MAX_CSV_BYTES + 1)
        request_id = request_id_from(request)
        try:
            result = commit_catalog_import(
                content=content,
                original_filename=upload.name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
                expected_sha256=data["sha256"],
                idempotency_key=data["idempotency_key"],
                user=request.user,
                relations=catalog_relation_index_for(request.user),
                request_id=request_id,
            )
        except CatalogImportCommitError as error:
            response = Response(
                {
                    "code": error.code,
                    "message": error.message,
                    "field_errors": error.field_errors,
                    "request_id": request_id,
                },
                status=error.status_code,
            )
            response["Cache-Control"] = "no-store"
            return response

        batch = result.batch
        payload = CatalogImportCommitResponseSerializer(
            {
                "id": batch.pk,
                "status": batch.status,
                "replayed": result.replayed,
                "sha256": batch.sha256,
                "row_count": batch.row_count,
                "warning_count": batch.warning_count,
                "create_count": batch.create_count,
                "update_count": batch.update_count,
                "archive_count": batch.archive_count,
                "committed_at": batch.committed_at,
            }
        ).data
        response = Response(
            payload,
            status=status.HTTP_200_OK if result.replayed else status.HTTP_201_CREATED,
        )
        response["Cache-Control"] = "no-store"
        return response
