from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.accounts.permissions import AdminAction, HasAdminAction, has_admin_action
from modules.audit.request_id import request_id_from

from .models import EditorialRevision, PublicationVersion
from .publication import publish_revision, restore_publication
from .serializers import (
    CreateEditorialRevisionSerializer,
    EditorialRevisionSerializer,
    EditorialWorkflowErrorSerializer,
    PublicationVersionSerializer,
    PublishEditorialRevisionSerializer,
    RestorePublicationVersionSerializer,
    ReturnEditorialRevisionSerializer,
    RevisionTransitionSerializer,
    UpdateEditorialRevisionSerializer,
)
from .workflow import (
    EditorialWorkflowError,
    approve_revision,
    create_revision,
    resolve_target_region,
    return_revision,
    submit_revision,
    update_revision,
)


def _workflow_error(error: EditorialWorkflowError, *, request_id) -> Response:
    return Response(
        {
            "code": error.code,
            "message": error.message,
            "field_errors": error.field_errors,
            "request_id": str(request_id),
        },
        status=error.status_code,
    )


def _revision_for_user(request: Request, revision_id, action: AdminAction) -> EditorialRevision:
    revision = get_object_or_404(
        EditorialRevision.objects.select_related("region"),
        pk=revision_id,
    )
    if not has_admin_action(request.user, action, region=revision.region):
        raise PermissionDenied("Você não tem acesso a esta revisão editorial.")
    return revision


def _publication_for_user(
    request: Request,
    publication_id,
    action: AdminAction,
) -> PublicationVersion:
    publication = get_object_or_404(
        PublicationVersion.objects.select_related("region"),
        pk=publication_id,
    )
    if not has_admin_action(request.user, action, region=publication.region):
        raise PermissionDenied("Você não tem acesso a esta publicação.")
    return publication


class EditorialRevisionCreateView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.EDIT_CONTENT

    @extend_schema(
        operation_id="createEditorialRevision",
        tags=["Admin editorial"],
        request=CreateEditorialRevisionSerializer,
        responses={
            201: EditorialRevisionSerializer,
            400: EditorialWorkflowErrorSerializer,
            403: EditorialWorkflowErrorSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = CreateEditorialRevisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            region = resolve_target_region(
                target_type=data["target_type"],
                target_id=data["target_id"],
                actor_region_id=data.get("region_id"),
            )
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except EditorialWorkflowError as error:
            return _workflow_error(error, request_id=request_id_from(request))
        if not has_admin_action(request.user, AdminAction.EDIT_CONTENT, region=region):
            raise PermissionDenied("Você não tem acesso à região deste conteúdo.")
        try:
            revision = create_revision(
                target_type=data["target_type"],
                target_id=data["target_id"],
                actor_region_id=data.get("region_id"),
                snapshot=data["snapshot"],
                user=request.user,
            )
        except EditorialWorkflowError as error:
            return _workflow_error(error, request_id=request_id_from(request))
        return Response(
            EditorialRevisionSerializer(revision).data,
            status=status.HTTP_201_CREATED,
        )


class EditorialRevisionDetailView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.EDIT_CONTENT

    @extend_schema(
        operation_id="retrieveEditorialRevision",
        tags=["Admin editorial"],
        responses={200: EditorialRevisionSerializer},
    )
    def get(self, request: Request, revision_id) -> Response:
        revision = _revision_for_user(
            request,
            revision_id,
            AdminAction.EDIT_CONTENT,
        )
        return Response(EditorialRevisionSerializer(revision).data)

    @extend_schema(
        operation_id="updateEditorialRevision",
        tags=["Admin editorial"],
        request=UpdateEditorialRevisionSerializer,
        responses={
            200: EditorialRevisionSerializer,
            409: EditorialWorkflowErrorSerializer,
        },
    )
    def patch(self, request: Request, revision_id) -> Response:
        _revision_for_user(request, revision_id, AdminAction.EDIT_CONTENT)
        serializer = UpdateEditorialRevisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            revision = update_revision(
                revision_id=revision_id,
                snapshot=serializer.validated_data["snapshot"],
                expected_lock_version=serializer.validated_data["lock_version"],
                user=request.user,
            )
        except EditorialWorkflowError as error:
            return _workflow_error(error, request_id=request_id_from(request))
        return Response(EditorialRevisionSerializer(revision).data)


class EditorialRevisionSubmitView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.EDIT_CONTENT

    @extend_schema(
        operation_id="submitEditorialRevision",
        tags=["Admin editorial"],
        request=RevisionTransitionSerializer,
        responses={
            200: EditorialRevisionSerializer,
            409: EditorialWorkflowErrorSerializer,
        },
    )
    def post(self, request: Request, revision_id) -> Response:
        _revision_for_user(request, revision_id, AdminAction.EDIT_CONTENT)
        serializer = RevisionTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            revision = submit_revision(
                revision_id=revision_id,
                expected_lock_version=serializer.validated_data["lock_version"],
                user=request.user,
            )
        except EditorialWorkflowError as error:
            return _workflow_error(error, request_id=request_id_from(request))
        return Response(EditorialRevisionSerializer(revision).data)


class EditorialRevisionReturnView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.APPROVE

    @extend_schema(
        operation_id="returnEditorialRevision",
        tags=["Admin editorial"],
        request=ReturnEditorialRevisionSerializer,
        responses={
            200: EditorialRevisionSerializer,
            409: EditorialWorkflowErrorSerializer,
        },
    )
    def post(self, request: Request, revision_id) -> Response:
        _revision_for_user(request, revision_id, AdminAction.APPROVE)
        serializer = ReturnEditorialRevisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            revision = return_revision(
                revision_id=revision_id,
                expected_lock_version=serializer.validated_data["lock_version"],
                reason=serializer.validated_data["reason"],
                user=request.user,
            )
        except EditorialWorkflowError as error:
            return _workflow_error(error, request_id=request_id_from(request))
        return Response(EditorialRevisionSerializer(revision).data)


class EditorialRevisionApproveView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.APPROVE

    @extend_schema(
        operation_id="approveEditorialRevision",
        tags=["Admin editorial"],
        request=RevisionTransitionSerializer,
        responses={
            200: EditorialRevisionSerializer,
            403: EditorialWorkflowErrorSerializer,
            409: EditorialWorkflowErrorSerializer,
        },
    )
    def post(self, request: Request, revision_id) -> Response:
        _revision_for_user(request, revision_id, AdminAction.APPROVE)
        serializer = RevisionTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            revision = approve_revision(
                revision_id=revision_id,
                expected_lock_version=serializer.validated_data["lock_version"],
                user=request.user,
                request_id=request_id_from(request),
            )
        except EditorialWorkflowError as error:
            return _workflow_error(error, request_id=request_id_from(request))
        return Response(EditorialRevisionSerializer(revision).data)


class EditorialRevisionPublishView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.PUBLISH

    @extend_schema(
        operation_id="publishEditorialRevision",
        tags=["Admin editorial"],
        request=PublishEditorialRevisionSerializer,
        responses={
            200: PublicationVersionSerializer,
            400: EditorialWorkflowErrorSerializer,
            403: EditorialWorkflowErrorSerializer,
            409: EditorialWorkflowErrorSerializer,
        },
    )
    def post(self, request: Request, revision_id) -> Response:
        _revision_for_user(request, revision_id, AdminAction.PUBLISH)
        serializer = PublishEditorialRevisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            publication = publish_revision(
                revision_id=revision_id,
                expected_lock_version=data["lock_version"],
                publisher=request.user,
                reason=data.get("reason", ""),
                source_confirmed=data["source_confirmed"],
                human_confirmed=data["human_confirmed"],
                critical_information_current=data["critical_information_current"],
                critical_override_reason=data.get(
                    "critical_override_reason",
                    "",
                ),
                request_id=request_id_from(request),
            )
        except EditorialWorkflowError as error:
            return _workflow_error(error, request_id=request_id_from(request))
        return Response(PublicationVersionSerializer(publication).data)


class PublicationVersionRestoreView(APIView):
    permission_classes = [HasAdminAction]
    required_admin_action = AdminAction.PUBLISH

    @extend_schema(
        operation_id="restorePublicationVersion",
        tags=["Admin editorial"],
        request=RestorePublicationVersionSerializer,
        responses={
            200: PublicationVersionSerializer,
            400: EditorialWorkflowErrorSerializer,
            403: EditorialWorkflowErrorSerializer,
            409: EditorialWorkflowErrorSerializer,
        },
    )
    def post(self, request: Request, publication_id) -> Response:
        _publication_for_user(request, publication_id, AdminAction.PUBLISH)
        serializer = RestorePublicationVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            publication = restore_publication(
                source_publication_id=publication_id,
                expected_current_version=data["expected_current_version"],
                restorer=request.user,
                reason=data["reason"],
                source_confirmed=data["source_confirmed"],
                human_confirmed=data["human_confirmed"],
                critical_information_current=data["critical_information_current"],
                critical_override_reason=data.get("critical_override_reason", ""),
                request_id=request_id_from(request),
            )
        except EditorialWorkflowError as error:
            return _workflow_error(error, request_id=request_id_from(request))
        return Response(PublicationVersionSerializer(publication).data)
