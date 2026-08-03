from importlib import import_module


def test_rls_migration_covers_all_django_tables_without_public_policies():
    migration = import_module("modules.routes.migrations.0002_enable_rls")
    sql = migration.rls_statements("ENABLE")

    assert len(migration.DJANGO_TABLES) == 20
    assert 'ALTER TABLE public."auth_user" ENABLE ROW LEVEL SECURITY;' in sql
    assert 'ALTER TABLE public."django_session" ENABLE ROW LEVEL SECURITY;' in sql
    assert 'ALTER TABLE public."regions_region" ENABLE ROW LEVEL SECURITY;' in sql
    assert 'ALTER TABLE public."routes_route" ENABLE ROW LEVEL SECURITY;' in sql
    assert 'ALTER TABLE public."catalog_actor" ENABLE ROW LEVEL SECURITY;' in sql
    assert "CREATE POLICY" not in sql
    assert "GRANT " not in sql


def test_rls_migration_covers_analytics_and_reports_tables():
    analytics_migration = import_module("modules.analytics.migrations.0002_enable_rls")
    analytics_sql = analytics_migration.rls_statements("ENABLE")
    assert (
        'ALTER TABLE public."analytics_rawanalyticsevent" ENABLE ROW LEVEL SECURITY;'
        in analytics_sql
    )
    assert (
        'ALTER TABLE public."analytics_dailyanalyticsaggregate" ENABLE ROW LEVEL SECURITY;'
        in analytics_sql
    )
    assert "CREATE POLICY" not in analytics_sql

    reports_migration = import_module("modules.reports.migrations.0002_enable_rls")
    reports_sql = reports_migration.rls_statements("ENABLE")
    assert 'ALTER TABLE public."reports_publicreport" ENABLE ROW LEVEL SECURITY;' in reports_sql
    assert "CREATE POLICY" not in reports_sql
