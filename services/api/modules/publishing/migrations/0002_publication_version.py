import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def enable_rls(_apps, schema_editor) -> None:
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            'ALTER TABLE public."publishing_publicationversion" ENABLE ROW LEVEL SECURITY;'
        )


def disable_rls(_apps, schema_editor) -> None:
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            'ALTER TABLE public."publishing_publicationversion" DISABLE ROW LEVEL SECURITY;'
        )


class Migration(migrations.Migration):
    dependencies = [
        ("publishing", "0001_editorial_revision"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="editorialrevision",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Rascunho"),
                    ("review", "Em revisão"),
                    ("approved", "Aprovado"),
                    ("published", "Publicado"),
                ],
                db_index=True,
                default="draft",
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="PublicationVersion",
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
                ("version", models.PositiveIntegerField()),
                ("snapshot", models.JSONField()),
                ("checksum", models.CharField(db_index=True, max_length=64)),
                ("reason", models.TextField(blank=True)),
                ("source_confirmed", models.BooleanField()),
                ("human_confirmed", models.BooleanField()),
                ("critical_information_current", models.BooleanField()),
                ("critical_override_reason", models.TextField(blank=True)),
                ("published_at", models.DateTimeField()),
                (
                    "approved_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="approved_publication_versions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "published_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_publication_versions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication_versions",
                        to="regions.region",
                    ),
                ),
                (
                    "revision",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication",
                        to="publishing.editorialrevision",
                    ),
                ),
            ],
            options={
                "ordering": ("target_type", "target_id", "-version"),
                "indexes": [
                    models.Index(
                        fields=["region", "published_at"],
                        name="publication_region_date_idx",
                    ),
                    models.Index(
                        fields=["target_type", "target_id", "published_at"],
                        name="publication_target_date_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("target_type", "target_id", "version"),
                        name="publication_target_version_uniq",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("version__gt", 0)),
                        name="publication_version_positive",
                    ),
                ],
            },
        ),
        migrations.RunPython(enable_rls, disable_rls),
    ]
