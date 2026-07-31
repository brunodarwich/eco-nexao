import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

ROLE_GROUPS = (
    "econexao:editor",
    "econexao:reviewer",
    "econexao:publisher",
    "econexao:analyst",
    "econexao:administrator",
)


def create_role_groups(apps, _schema_editor) -> None:
    group_model = apps.get_model("auth", "Group")
    for name in ROLE_GROUPS:
        group_model.objects.get_or_create(name=name)


def delete_role_groups(apps, _schema_editor) -> None:
    group_model = apps.get_model("auth", "Group")
    group_model.objects.filter(name__in=ROLE_GROUPS).delete()


def enable_rls(_apps, schema_editor) -> None:
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            'ALTER TABLE public."accounts_administrativeregionscope" ENABLE ROW LEVEL SECURITY;'
        )


def disable_rls(_apps, schema_editor) -> None:
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            'ALTER TABLE public."accounts_administrativeregionscope" DISABLE ROW LEVEL SECURITY;'
        )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("regions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdministrativeRegionScope",
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
                ("is_active", models.BooleanField(default=True)),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="administrative_user_scopes",
                        to="regions.region",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="administrative_region_scopes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("user_id", "region_id"),
                "indexes": [
                    models.Index(
                        fields=["user", "is_active"],
                        name="admin_scope_user_active_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("user", "region"),
                        name="admin_scope_user_region_uniq",
                    ),
                ],
            },
        ),
        migrations.RunPython(create_role_groups, delete_role_groups),
        migrations.RunPython(enable_rls, disable_rls),
    ]
