"""
Django settings for thinky project.
"""

from pathlib import Path
from datetime import timedelta
import os

from dotenv import load_dotenv
import os

# 🌟 تفعيل قراءة ملف .env فوراً عند إقلاع السيرفر
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-bmq-e)rb8oyc90!7^nsoy3!bq7aw91$)&3c4h=jj#0+$wgfeti',
)

DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', '').split(',')
    if host.strip()
]
railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
render_domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if railway_domain:
    ALLOWED_HOSTS.append(railway_domain)
if render_domain:
    ALLOWED_HOSTS.append(render_domain)
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1'] if DEBUG else ['*']

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
if railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{railway_domain}')
render_url = os.environ.get('RENDER_EXTERNAL_URL')
if render_url:
    CSRF_TRUSTED_ORIGINS.append(render_url.rstrip('/'))
elif render_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{render_domain}')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

INSTALLED_APPS = [
    'drf_spectacular',
    'users',
    'levels',
    'questions',
    'game_sessions',
    'answers',
    'store',
    'ai_engine',
    'points',
    "user_store",
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'thinky.urls'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=365),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'thinky.wsgi.application'

AUTH_USER_MODEL = 'users.User'

_db_dir = os.environ.get('DATABASE_DIR') or os.environ.get('RAILWAY_VOLUME_MOUNT_PATH') or BASE_DIR
_database_url = os.environ.get('DATABASE_URL')

if _database_url:
    import dj_database_url

    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': Path(_db_dir) / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
