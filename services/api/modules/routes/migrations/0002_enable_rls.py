from django.db import migrations

DJANGO_TABLES = (
    "django_migrations",
    "django_content_type",
    "auth_permission",
    "auth_group",
    "auth_group_permissions",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
    "django_session",
    "regions_region",
    "routes_route",
    "routes_routestage",
    "routes_routesegment",
    "routes_alert",
    "catalog_category",
    "catalog_actor",
    "catalog_actorlocation",
    "catalog_contactchannel",
    "catalog_operatinghours",
    "catalog_routeactor",
)


def rls_statements(action: str) -> str:
    return "\n".join(
        f'ALTER TABLE public."{table}" {action} ROW LEVEL SECURITY;' for table in DJANGO_TABLES
    )


def apply_rls(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(rls_statements("ENABLE"))


def revert_rls(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(rls_statements("DISABLE"))


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("catalog", "0001_initial"),
        ("routes", "0001_initial"),
        ("sessions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            code=apply_rls,
            reverse_code=revert_rls,
        ),
    ]
