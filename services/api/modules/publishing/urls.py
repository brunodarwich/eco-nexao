from django.urls import path

from .views import (
    EditorialRevisionApproveView,
    EditorialRevisionCreateView,
    EditorialRevisionDetailView,
    EditorialRevisionPublishView,
    EditorialRevisionReturnView,
    EditorialRevisionSubmitView,
    PublicationVersionRestoreView,
)

urlpatterns = [
    path(
        "revisions",
        EditorialRevisionCreateView.as_view(),
        name="editorial-revision-create",
    ),
    path(
        "revisions/<uuid:revision_id>",
        EditorialRevisionDetailView.as_view(),
        name="editorial-revision-detail",
    ),
    path(
        "revisions/<uuid:revision_id>/submit",
        EditorialRevisionSubmitView.as_view(),
        name="editorial-revision-submit",
    ),
    path(
        "revisions/<uuid:revision_id>/return",
        EditorialRevisionReturnView.as_view(),
        name="editorial-revision-return",
    ),
    path(
        "revisions/<uuid:revision_id>/approve",
        EditorialRevisionApproveView.as_view(),
        name="editorial-revision-approve",
    ),
    path(
        "revisions/<uuid:revision_id>/publish",
        EditorialRevisionPublishView.as_view(),
        name="editorial-revision-publish",
    ),
    path(
        "publications/<uuid:publication_id>/restore",
        PublicationVersionRestoreView.as_view(),
        name="publication-version-restore",
    ),
]
