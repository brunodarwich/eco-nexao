from pathlib import Path

import dj_database_url

SUPPORTED_DATABASE_ENGINES = {
    "postgresql": "django.db.backends.postgresql",
    "postgis": "django.contrib.gis.db.backends.postgis",
    "spatialite": "django.contrib.gis.db.backends.spatialite",
}


def build_database_config(
    database_url: str | None,
    database_engine: str,
    base_dir: Path,
) -> dict:
    if not database_url:
        config = dj_database_url.parse(f"sqlite:///{base_dir / 'db.sqlite3'}")
        config["ENGINE"] = "django.contrib.gis.db.backends.spatialite"
        return config

    try:
        engine = SUPPORTED_DATABASE_ENGINES[database_engine]
    except KeyError as error:
        supported = ", ".join(sorted(SUPPORTED_DATABASE_ENGINES))
        raise ValueError(
            f"DATABASE_ENGINE inválido: {database_engine}. Use: {supported}."
        ) from error

    config = dj_database_url.parse(database_url, conn_max_age=60)
    config["ENGINE"] = engine
    return config
