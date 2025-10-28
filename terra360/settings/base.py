# abmci/settings/base.py
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from datetime import timedelta
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from celery.schedules import crontab
from firebase_admin import credentials  # si tu l'utilises réellement (sinon à commenter)

BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ========== Helpers ==========
def env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return str(val).lower() in ("1", "true", "yes", "on")


def env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    try:
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _split_csv_env(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _with_scheme(origin: str) -> str:
    # si déjà un schéma → OK
    if origin.startswith(("http://", "https://")):
        return origin
    # localhost + IP → http par défaut (dev)
    if origin in ("localhost",) or re.match(r"^\d{1,3}(\.\d{1,3}){3}$", origin):
        return f"http://{origin}"
    # par défaut pour un domaine → https
    return f"https://{origin}"


# ========== Core ==========
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = env_bool("DEBUG", False)

LANGUAGE_CODE = "fr-FR"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True

SITE_ID = int(os.getenv("SITE_ID", "1"))

ALLOWED_HOSTS = _split_csv_env("ALLOWED_HOSTS")  # ex: admin.example.com,example.com,127.0.0.1,localhost

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.gis",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",

    # 3rd-party
    "simple_history",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "django_filters",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "qr_code",
    "crispy_forms",
    "crispy_bootstrap4",
    "notifications",
    "channels",
    "django_select2",
    "django_countries",
    "drf_yasg",
    "django_celery_beat",
    "widget_tweaks",
    "tinymce",

    # Storages (activé si MINIO_ENABLED)
    "storages",

    # Apps projet
    "accounts",
    "billing",
    "leasing",
    "maintenance",
    "parties",
    "payments",
    "properties",
    "public_api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise (ok prod & dev pour servir les statiques si pas de proxy frontal)
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "terra360.urls"
WSGI_APPLICATION = "terra360.wsgi.application"
ASGI_APPLICATION = "terra360.asgi.application"

AUTH_USER_MODEL = "accounts.User"

# ========== Templates ==========
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

# ========== Database ==========
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DB_NAME", "terra360"),
        "USER": os.getenv("DB_USER", "terra360"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# ========== Auth ==========
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "account_login"

ACCOUNT_LOGIN_METHODS = {"email"}  # ou {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]  # * = requis
ACCOUNT_UNIQUE_EMAIL = True
# ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # ou "optional"

# ========== DRF / JWT ==========
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": env_int("PAGE_SIZE", 100),
}

REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": None,  # mobile : pas de cookie
    "JWT_AUTH_REFRESH_COOKIE": None,
    "PASSWORD_RESET_USE_SITES_DOMAIN": True,
    "PASSWORD_RESET_CONFIRM_URL": "auth/password/reset/confirm/{uid}/{token}/",
    "USER_DETAILS_SERIALIZER": "api.serializers.CustomUserDetailsSerializer",
    "REGISTER_SERIALIZER": "api.serializers.CustomRegisterSerializer",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MIN", 60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_DAYS", 7)),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ========== CORS / CSRF ==========
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [_with_scheme(o) for o in _split_csv_env("CORS_ALLOWED_ORIGINS")]
CSRF_TRUSTED_ORIGINS = [_with_scheme(o) for o in _split_csv_env("CSRF_TRUSTED_ORIGINS")]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ========== Static & Media ==========
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# WhiteNoise: compression + manifest
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ========== MinIO / S3 (django-storages) ==========
MINIO_ENABLED = env_bool("MINIO_ENABLED", True)
if MINIO_ENABLED:
    # Active la storage backend S3
    STORAGES["default"] = {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", os.getenv("MINIO_ROOT_USER", "minioadmin"))
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"))
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "media")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "http://minio:9000")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_SIGNATURE_VERSION = os.getenv("AWS_S3_SIGNATURE_VERSION", "s3v4")
    AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "path")  # 'auto' | 'virtual' | 'path'
    AWS_S3_VERIFY = env_bool("AWS_S3_VERIFY", False)
    AWS_QUERYSTRING_AUTH = env_bool("AWS_QUERYSTRING_AUTH", False)  # False → URLs simples si bucket public
    AWS_DEFAULT_ACL = os.getenv("AWS_DEFAULT_ACL", "public-read")  # si bucket rendu public par policy

    # Domaine public (si tu frontes MinIO derrière un domaine/CDN)
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN")  # ex: cdn.example.com
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

# ========== Emails ==========
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = env_int("EMAIL_PORT", 465)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")

# ========== Sessions / Sécurité ==========
SESSION_COOKIE_AGE = env_int("SESSION_COOKIE_AGE", 60 * 60 * 24 * 30)  # 30 jours
CSRF_COOKIE_AGE = env_int("CSRF_COOKIE_AGE", 60 * 60 * 24 * 7)  # 7 jours
PASSWORD_RESET_TIMEOUT = env_int("PASSWORD_RESET_TIMEOUT", 60 * 60 * 24 * 3)

# Cookies sécurisés en prod
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)

# HSTS (uniquement si HTTPS correct devant)
SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000 if not DEBUG else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", not DEBUG)

# ========== Channels ==========
# Fallback InMemory si pas de Redis configuré
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = env_int("REDIS_PORT", 6379)
USE_CHANNELS_REDIS = env_bool("USE_CHANNELS_REDIS", True)

if USE_CHANNELS_REDIS:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [(REDIS_HOST, REDIS_PORT)]},
        }
    }
else:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# ========== Celery ==========
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

CELERY_BEAT_SCHEDULE = {
    # garde ce qui existe déjà si tes tâches sont présentes
    "push_verse_of_day_daily": {
        "task": "abmci.push_vod_daily",
        "schedule": crontab(minute=0, hour=6),
    },
    "remind-stale-problems-every-hour": {
        "task": "problems.tasks.remind_stale_problems",
        "schedule": crontab(minute=0),
        "args": (env_int("PROBLEM_REMINDER_DELAY_H", 48),),
    },
    "send-daily-vod-0730": {
        "task": "vod.tasks.send_daily_vod",
        "schedule": crontab(minute=30, hour=6),
        "args": (),
    },
}

# ========== Paystack ==========
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "pk_live_xxx")
PAYSTACK_BASE_URL = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
PAYSTACK_ALLOWED_CURRENCIES = {"XOF", "NGN"}
SITE_URL = os.getenv("SITE_URL", "https://administration.abmci.com/api")
PAYSTACK_IPS_WHITELIST = set()  # optionnel : à remplir si tu filtres par IP

# ========== TinyMCE ==========
TINYMCE_DEFAULT_CONFIG = {
    "height": 400,
    "menubar": False,
    "plugins": "link lists table code image",
    "toolbar": (
        "undo redo | styles | bold italic underline | "
        "alignleft aligncenter alignright | bullist numlist | "
        "link image table | code"
    ),
    "block_formats": "Paragraph=p; Heading 2=h2; Heading 3=h3",
    "cleanup_on_startup": True,
    "convert_urls": False,
}

# ========== Orange SMS / Meta WA ==========
ORANGE_TOKEN_URL = os.getenv("ORANGE_TOKEN_URL", "https://api.orange.com/oauth/v3/token")
ORANGE_SMS_URL = os.getenv("ORANGE_SMS_URL", "https://api.orange.com/smsmessaging/v1/outbound/{}/requests")
ORANGE_SMS_CLIENT_ID = os.getenv("ORANGE_SMS_CLIENT_ID", "")
ORANGE_SMS_CLIENT_SECRET = os.getenv("ORANGE_SMS_CLIENT_SECRET", "")
ORANGE_SMS_SENDER = os.getenv("ORANGE_SMS_SENDER", "")  # ex: tel:+225734201

META_WA_API_VERSION = os.getenv("META_WA_API_VERSION", "v20.0")
META_WA_BASE_URL = os.getenv("META_WA_BASE_URL", "https://graph.facebook.com")
META_WA_PHONE_NUMBER_ID = os.getenv("META_WA_PHONE_NUMBER_ID", "")
META_WA_ACCESS_TOKEN = os.getenv("META_WA_ACCESS_TOKEN", "")

# ========== Firebase (optionnel) ==========
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")  # ex: /run/secrets/firebase.json
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")  # base64 OU JSON brut
FIREBASE_SERVICE_ACCOUNT_DICT = None
if FIREBASE_SERVICE_ACCOUNT_JSON:
    try:
        # accepte du base64 ou du JSON brut
        try:
            decoded = base64.b64decode(FIREBASE_SERVICE_ACCOUNT_JSON).decode("utf-8")
            FIREBASE_SERVICE_ACCOUNT_DICT = json.loads(decoded)
        except Exception:
            FIREBASE_SERVICE_ACCOUNT_DICT = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
    except Exception:
        FIREBASE_SERVICE_ACCOUNT_DICT = None

# ========== Sentry (optionnel) ==========
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    try:
        from sentry_sdk.integrations.celery import CeleryIntegration
    except Exception:
        CeleryIntegration = None
    try:
        from sentry_sdk.integrations.redis import RedisIntegration
    except Exception:
        RedisIntegration = None

    _integrations = [DjangoIntegration()]
    if CeleryIntegration:
        _integrations.append(CeleryIntegration())
    if RedisIntegration:
        _integrations.append(RedisIntegration())

    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=_integrations,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=True,
        )
except Exception as _sentry_e:  # silencieux si non configuré
    pass

# ========== Logging ==========
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

# ========== Divers ==========
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ORIGIN = os.getenv("SITE_ORIGIN", "https://api-immobilier.afriqconsulting.site")
