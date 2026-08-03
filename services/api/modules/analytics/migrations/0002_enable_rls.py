from django.db import migrations

ANALYTICS_TABLES = (
    "analytics_rawanalyticsevent",
    "analytics_dailyanalyticsaggregate",
)


def rls_statements(action: str) -> str:
    return "\n".join(
        f'ALTER TABLE public."{table}" {action} ROW LEVEL SECURITY;' for table in ANALYTICS_TABLES
    )


def apply_rls(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(rls_statements("ENABLE"))


def revert_rls(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(rls_statements("DISABLE"))


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            code=apply_rls,
            reverse_code=revert_rls,
        ),
    ]
