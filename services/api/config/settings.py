import os
from ctypes import CDLL
from pathlib import Path

from .database import build_database_config

BASE_DIR = Path(__file__).resolve().parent.parent

OSGEO4W_BIN = Path(r"C:\OSGeo4W\bin")
if os.name == "nt" and OSGEO4W_BIN.is_dir():
    os.environ["PATH"] = str(OSGEO4W_BIN) + os.pathsep + os.environ.get("PATH", "")

OSGEO4W_DLL_DIRECTORY = (
    os.add_dll_directory(str(OSGEO4W_BIN)) if os.name == "nt" and OSGEO4W_BIN.is_dir() else None
)
GDAL_LIBRARY_PATH = os.getenv("GDAL_LIBRARY_PATH") or next(
    (library for library in ("gdal311.dll", "gdal310.dll") if (OSGEO4W_BIN / library).is_file()),
    None,
)
GEOS_LIBRARY_PATH = os.getenv("GEOS_LIBRARY_PATH") or (
    "geos_c.dll" if (OSGEO4W_BIN / "geos_c.dll").is_file() else None
)
SPATIALITE_LIBRARY_PATH = os.getenv("SPATIALITE_LIBRARY_PATH") or (
    "mod_spatialite.dll" if (OSGEO4W_BIN / "mod_spatialite.dll").is_file() else None
)
OSGEO4W_GDAL_HANDLE = (
    CDLL(GDAL_LIBRARY_PATH)
    if os.name == "nt" and OSGEO4W_DLL_DIRECTORY and GDAL_LIBRARY_PATH
    else None
)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-local-development-key")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,.loca.lt,.vercel.app,.trycloudflare.com").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://localhost:3001,https://*.vercel.app,https://*.loca.lt,https://*.trycloudflare.com",
    ).split(",")
    if origin.strip()
]
SECURE_COOKIES = os.getenv("DJANGO_SECURE_COOKIES", str(not DEBUG)).lower() == "true"
GOOGLE_PLACES_ADMIN_PREVIEW_ENABLED = (
    os.getenv("GOOGLE_PLACES_ADMIN_PREVIEW_ENABLED", "false").lower() == "true"
)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv(
    "GOOGLE_PLACES_API_KEY",
    "",
)

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "drf_spectacular",
    "modules.accounts",
    "modules.analytics",
    "modules.audit",
    "modules.catalog",
    "modules.health",
    "modules.imports",
    "modules.publishing",
    "modules.regions",
    "modules.reports",
    "modules.routes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "modules.audit.request_id.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": build_database_config(
        database_url=os.getenv("DATABASE_URL"),
        database_engine=os.getenv("DATABASE_ENGINE", "postgresql"),
        base_dir=BASE_DIR,
    )
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_NAME = "econexao_admin_sessionid"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = SECURE_COOKIES
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

CSRF_COOKIE_NAME = "econexao_admin_csrftoken"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = SECURE_COOKIES
CSRF_FAILURE_VIEW = "modules.accounts.views.csrf_failure"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_RATES": {
        "google_places_preview": os.getenv(
            "GOOGLE_PLACES_PREVIEW_RATE",
            "10/hour",
        ),
        "csv_validation": os.getenv("CSV_VALIDATION_RATE", "30/hour"),
        "public_reports": os.getenv("PUBLIC_REPORTS_RATE", "5/hour"),
        "analytics_batch": os.getenv("ANALYTICS_BATCH_RATE", "60/hour"),
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ECOnexão API",
    "DESCRIPTION": "API pública e administrativa versionada da ECOnexão.",
    "VERSION": "1.0.0",
}
