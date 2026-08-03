from pathlib import Path

import pytest

from config.database import build_database_config


def test_uses_sqlite_when_database_url_is_absent(tmp_path: Path):
    config = build_database_config(None, "postgresql", tmp_path)

    assert config["ENGINE"] == "django.contrib.gis.db.backends.spatialite"
    assert config["NAME"] == str(tmp_path / "db.sqlite3")


@pytest.mark.parametrize(
    ("database_engine", "expected_backend"),
    [
        ("postgresql", "django.db.backends.postgresql"),
        ("postgis", "django.contrib.gis.db.backends.postgis"),
    ],
)
def test_configures_supabase_backends(database_engine: str, expected_backend: str):
    config = build_database_config(
        "postgresql://postgres.project:password@pooler.example.com:5432/postgres?sslmode=require",
        database_engine,
        Path("."),
    )

    assert config["ENGINE"] == expected_backend
    assert config["OPTIONS"]["sslmode"] == "require"
    assert config["CONN_MAX_AGE"] == 60


def test_rejects_unknown_database_engine():
    with pytest.raises(ValueError, match="DATABASE_ENGINE inválido"):
        build_database_config(
            "postgresql://postgres:password@localhost:5432/postgres",
            "unknown",
            Path("."),
        )
