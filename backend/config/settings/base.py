import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-insecure-key-change-in-production")

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

DJANGO_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.core",
    "apps.workspace",
    "apps.ai",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="flux"),
        "USER": config("DB_USER", default="flux"),
        "PASSWORD": config("DB_PASSWORD", default="flux"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "MAX_PAGE_SIZE": 100,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {"ai": config("AI_RATE_LIMIT", default="20/min")},
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Flux API",
    "DESCRIPTION": "Flux productivity workspace API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Celery (Redis is the broker only; the app cache stays client side in TanStack Query)
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6380/0")
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool)
CELERY_TASK_IGNORE_RESULT = True

# AI features
AI_EMBEDDINGS_ENABLED = config("AI_EMBEDDINGS_ENABLED", default=True, cast=bool)
AI_ENABLED = config("AI_ENABLED", default=False, cast=bool)
ANTHROPIC_API_KEY = config("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = config("ANTHROPIC_MODEL", default="claude-sonnet-5-5")
AI_MAX_TOKENS = config("AI_MAX_TOKENS", default=2048, cast=int)
AI_MAX_ITERATIONS = config("AI_MAX_ITERATIONS", default=6, cast=int)
AI_PLAN_MAX_CARDS = config("AI_PLAN_MAX_CARDS", default=150, cast=int)
AI_RUN_STALE_SECONDS = config("AI_RUN_STALE_SECONDS", default=600, cast=int)
EMBEDDING_MODEL = config("EMBEDDING_MODEL", default="BAAI/bge-small-en-v1.5")
EMBEDDING_DIMENSIONS = 384
EMBEDDING_CACHE_DIR = config("EMBEDDING_CACHE_DIR", default="") or None
AI_SEARCH_LIMIT = config("AI_SEARCH_LIMIT", default=10, cast=int)
AI_SEARCH_MIN_SCORE = config("AI_SEARCH_MIN_SCORE", default=0.3, cast=float)

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
).split(",")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
