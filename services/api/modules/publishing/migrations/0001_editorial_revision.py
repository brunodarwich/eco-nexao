import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def enable_rls(_apps, schema_editor) -> None:
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            'ALTER TABLE public."publishing_editorialrevision" ENABLE ROW LEVEL SECURITY;'
        )


def disable_rls(_apps, schema_editor) -> None:
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            'ALTER TABLE public."publishing_editorialrevision" DISABLE ROW LEVEL SECURITY;'
        )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("regions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EditorialRevision",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "target_type",
                    models.CharField(
                        choices=[
                            ("region", "Região"),
                            ("route", "Rota"),
                            ("actor", "Ator"),
                        ],
                        max_length=16,
                    ),
                ),
                ("target_id", models.UUIDField()),
                ("sequence", models.PositiveIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Rascunho"),
                            ("review", "Em revisão"),
                            ("approved", "Aprovado"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("base_snapshot", models.JSONField(default=dict)),
                ("snapshot", models.JSONField(default=dict)),
                ("diff", models.JSONField(default=list)),
                ("lock_version", models.PositiveIntegerField(default=1)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("return_reason", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_editorial_revisions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="editorial_revisions",
                        to="regions.region",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reviewed_editorial_revisions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "submitted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="submitted_editorial_revisions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="updated_editorial_revisions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("target_type", "target_id", "-sequence"),
                "indexes": [
                    models.Index(
                        fields=["region", "status"],
                        name="revision_region_status_idx",
                    ),
                    models.Index(
                        fields=["target_type", "target_id", "status"],
                        name="revision_target_status_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("target_type", "target_id", "sequence"),
                        name="revision_target_sequence_uniq",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("sequence__gt", 0)),
                        name="revision_sequence_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("lock_version__gt", 0)),
                        name="revision_lock_version_positive",
                    ),
                ],
            },
        ),
        migrations.RunPython(enable_rls, disable_rls),
    ]
