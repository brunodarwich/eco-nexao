from django.db import migrations

REPORTS_TABLES = ("reports_publicreport",)


def rls_statements(action: str) -> str:
    return "\n".join(
        f'ALTER TABLE public."{table}" {action} ROW LEVEL SECURITY;' for table in REPORTS_TABLES
    )


def apply_rls(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(rls_statements("ENABLE"))


def revert_rls(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(rls_statements("DISABLE"))


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            code=apply_rls,
            reverse_code=revert_rls,
        ),
    ]
