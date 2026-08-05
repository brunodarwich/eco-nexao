import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def set_rls(schema_editor, action):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            'ALTER TABLE public."catalog_supportpointidempotencyrecord" '
            f"{action} ROW LEVEL SECURITY;"
        )


def enable_rls(_apps, schema_editor):
    set_rls(schema_editor, "ENABLE")


def disable_rls(_apps, schema_editor):
    set_rls(schema_editor, "DISABLE")


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0002_external_discovery"),
        ("regions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupportPointIdempotencyRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("idempotency_key", models.UUIDField(editable=False, unique=True)),
                ("request_fingerprint", models.CharField(max_length=64)),
                ("response_payload", models.JSONField()),
                ("expires_at", models.DateTimeField(db_index=True)),
                (
                    "actor",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="support_point_idempotency_record",
                        to="catalog.actor",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="support_point_idempotency_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="support_point_idempotency_records",
                        to="regions.region",
                    ),
                ),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
        migrations.AddIndex(
            model_name="supportpointidempotencyrecord",
            index=models.Index(
                fields=["created_by", "region", "expires_at"], name="support_idem_owner_exp_idx"
            ),
        ),
        migrations.RunPython(enable_rls, disable_rls),
    ]
