"""
Django settings for config project.
"""
import os
from pathlib import Path
import mimetypes

from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Security ───────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]   # hard-fail if missing — never fall back

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost 127.0.0.1").split()

# HTTPS / cookie hardening — only active in production (DEBUG=False)
ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    SECURE_SSL_REDIRECT            = True
    SECURE_HSTS_SECONDS            = 31536000   # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    X_FRAME_OPTIONS                = "DENY"
else:
    # Explicitly off in development — prevents browser HSTS cache issues
    SECURE_SSL_REDIRECT            = False
    SESSION_COOKIE_SECURE          = False
    CSRF_COOKIE_SECURE             = False

# ── Project ────────────────────────────────────────────────────────────────────

PROJECT_NAME = "Ace The Entrance"

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Auth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.twitter',

    # My Apps
    'home.apps.HomeConfig',
    'daily.apps.DailyConfig',
    'sxcmodel.apps.SxcmodelConfig',
    'discussion.apps.DiscussionConfig',
    'accounts.apps.AccountsConfig',
    'tos.apps.TosConfig',
    'about.apps.AboutConfig',
    'updates.apps.UpdatesConfig',
    'buy.apps.BuyConfig',

    # Third Party
    'django_crontab',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'home.context_processors.project_settings',
            ],
        },
    },
]

CACHES = {
    'default': {
        'BACKEND':  'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
    }
}

WSGI_APPLICATION = 'config.wsgi.application'

# ── Database ───────────────────────────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME'),
        'USER':     os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST':     os.getenv('DB_HOST'),
        'PORT':     os.getenv('DB_PORT'),
        'CONN_MAX_AGE': 60,   # persistent connections — good for production
    }
}

# ── Password validation ────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Auth / Allauth ─────────────────────────────────────────────────────────────

AUTH_USER_MODEL = 'accounts.User'

SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS      = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS      = ['email*', 'username*', 'firstname*', 'lastname*', 'dob*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_URL          = '/accounts/login/'
ACCOUNT_LOGOUT_URL         = '/accounts/logout/'
ACCOUNT_SIGNUP_URL         = '/accounts/signup/'
LOGIN_URL                  = '/accounts/login/'
LOGIN_REDIRECT_URL         = '/accounts/onboarding/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
SOCIALACCOUNT_LOGIN_ON_GET  = True
SOCIALACCOUNT_AUTO_SIGNUP   = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_EMAIL_VERIFICATION = True
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.SocialAccountAdapter'
SOCIALACCOUNT_DISCONNECT_REDIRECT_URL = '/accounts/dashboard/'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE    = 'Lax'
SOCIALACCOUNT_STORE_TOKENS = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': os.getenv('OAUTH_GOOGLE_CLIENT_ID'),
            'secret':    os.getenv('OAUTH_GOOGLE_CLIENT_SECRET'),
        }
    },
}

ACCOUNT_ADAPTER       = 'accounts.adapter.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapter.SocialAccountAdapter'

# ── Internationalisation ───────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

# ── Static & media ────────────────────────────────────────────────────────────

STATIC_URL  = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# ── Logging ───────────────────────────────────────────────────────────────────

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',   # INFO in dev, WARNING in prod is fine
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
    },
}

# ── Cron ──────────────────────────────────────────────────────────────────────

CRONJOBS = [
    ('1 0 * * *', 'django.core.management.call_command', ['create_daily_quiz'])
]

# ── Email ─────────────────────────────────────────────────────────────────────

EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.getenv('EMAIL')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')

# ── Misc ──────────────────────────────────────────────────────────────────────

mimetypes.add_type("application/manifest+json", ".webmanifest")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'