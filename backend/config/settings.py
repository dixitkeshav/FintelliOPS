from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Get values from the .env file
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-default-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Application definition
INSTALLED_APPS = [
    'daphne',
    'fetch_news',
    'intelligence',
    'agents',
    'quant',
    'pipelines',
    'evaluation',
    'cross_domain',
    'shock_predictor',
    'learning',
    'django_celery_beat',
    'rest_framework',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
_extra_cors = os.getenv("CORS_EXTRA_ORIGINS", "")
if _extra_cors:
    CORS_ALLOWED_ORIGINS.extend(
        origin.strip() for origin in _extra_cors.split(",") if origin.strip()
    )
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "true").lower() == "true"

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'news_api.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'fetch_news': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'fetch_news/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI / ASGI
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Redis (optional — omit on Render free tier; locmem + in-memory channels used instead)
REDIS_URL = os.getenv("REDIS_URL", "").strip() or (
    "redis://127.0.0.1:6379/0" if os.getenv("DJANGO_DEBUG", "True") == "True" else ""
)
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Feature flags (env-based)
FEATURE_GENAI_INSIGHTS = os.getenv("FEATURE_GENAI_INSIGHTS", "true").lower() == "true"
FEATURE_AGENTS = os.getenv("FEATURE_AGENTS", "true").lower() == "true"
FEATURE_QUANT_SIGNALS = os.getenv("FEATURE_QUANT_SIGNALS", "true").lower() == "true"
FEATURE_WEBSOCKETS = os.getenv("FEATURE_WEBSOCKETS", "true").lower() == "true"

# Channels (WebSockets) — Redis when configured, else in-memory (fine for free tier)
if REDIS_URL:
    try:
        import channels_redis  # noqa: F401

        CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG": {"hosts": [REDIS_URL]},
            }
        }
    except ImportError:
        CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
else:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# Database — shared PostgreSQL via DATABASE_URL (Render); SQLite for local dev without it
_database_url = os.getenv("DATABASE_URL", "").strip()
if _database_url:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=os.getenv("DATABASE_SSL", "true").lower() in ("1", "true", "yes"),
        )
    }
else:
    _db_name = os.getenv("DJANGO_DB_PATH")
    if _db_name:
        _db_name = Path(_db_name)
    else:
        _db_name = BASE_DIR / "db.sqlite3"
    _db_name.parent.mkdir(parents=True, exist_ok=True)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _db_name,
        }
    }

# Password Validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'Asia/Kolkata')
USE_I18N = True
USE_TZ = True

# Celery (after TIME_ZONE)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'shock-poll-and-score': {
        'task': 'shock_predictor.tasks.poll_and_score',
        'schedule': 30.0,
    },
    'shock-eod-feedback': {
        'task': 'shock_predictor.tasks.update_eod_feedback',
        'schedule': crontab(hour=15, minute=35),
    },
}

# Shock predictor integrations
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Static Files (CSS/JS)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'fetch_news/static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

ROOT_URLCONF = 'config.urls'

# Auto Field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
