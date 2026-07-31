import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

RLS_TABLES = (
    "catalog_externaldiscoveryrun",
    "catalog_externalsourcereference",
    "catalog_externaldiscoveryhit",
)


def set_rls(schema_editor, action: str) -> None:
    if schema_editor.connection.vendor != "postgresql":
        return
    for table in RLS_TABLES:
        schema_editor.execute(f'ALTER TABLE public."{table}" {action} ROW LEVEL SECURITY;')


def enable_rls(_apps, schema_editor) -> None:
    set_rls(schema_editor, "ENABLE")


def disable_rls(_apps, schema_editor) -> None:
    set_rls(schema_editor, "DISABLE")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExternalDiscoveryRun",
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
                    "provider",
                    models.CharField(
                        choices=[("google_places", "Google Places")],
                        max_length=32,
                    ),
                ),
                ("context_key", models.SlugField(max_length=160)),
                (
                    "center_latitude",
                    models.DecimalField(decimal_places=6, max_digits=9),
                ),
                (
                    "center_longitude",
                    models.DecimalField(decimal_places=6, max_digits=9),
                ),
                ("radius_meters", models.PositiveIntegerField()),
                ("included_types", models.JSONField(default=list)),
                ("max_results", models.PositiveSmallIntegerField()),
                ("result_count", models.PositiveSmallIntegerField()),
                (
                    "executed_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
            ],
            options={
                "ordering": ("-executed_at",),
            },
        ),
        migrations.CreateModel(
            name="ExternalSourceReference",
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
                    "provider",
                    models.CharField(
                        choices=[("google_places", "Google Places")],
                        max_length=32,
                    ),
                ),
                ("provider_record_id", models.CharField(max_length=255)),
                (
                    "review_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("researching", "Em apuração"),
                            ("linked", "Vinculado"),
                            ("rejected", "Descartado"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                (
                    "first_seen_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "last_seen_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="external_source_references",
                        to="catalog.actor",
                    ),
                ),
            ],
            options={
                "ordering": ("-last_seen_at", "provider_record_id"),
            },
        ),
        migrations.CreateModel(
            name="ExternalDiscoveryHit",
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
                ("result_position", models.PositiveSmallIntegerField()),
                (
                    "reference",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="discovery_hits",
                        to="catalog.externalsourcereference",
                    ),
                ),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hits",
                        to="catalog.externaldiscoveryrun",
                    ),
                ),
            ],
            options={
                "ordering": ("run_id", "result_position"),
            },
        ),
        migrations.AddIndex(
            model_name="externaldiscoveryrun",
            index=models.Index(
                fields=["provider", "context_key", "executed_at"],
                name="external_run_context_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="externalsourcereference",
            index=models.Index(
                fields=["provider", "last_seen_at"],
                name="external_source_seen_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="externalsourcereference",
            constraint=models.UniqueConstraint(
                fields=("provider", "provider_record_id"),
                name="external_source_provider_id_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="externaldiscoveryhit",
            constraint=models.UniqueConstraint(
                fields=("run", "reference"),
                name="external_hit_run_reference_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="externaldiscoveryhit",
            constraint=models.UniqueConstraint(
                fields=("run", "result_position"),
                name="external_hit_run_position_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="externaldiscoveryhit",
            constraint=models.CheckConstraint(
                condition=models.Q(("result_position__gt", 0)),
                name="external_hit_position_positive",
            ),
        ),
        migrations.RunPython(enable_rls, disable_rls),
    ]
