"""
Django settings for Mortgage Calculator project.
"""
import os
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# Security Settings
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', 'backend'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_celery_beat',

    # Local apps
    'api',
    'calculator',
    'documents',
    'scraper_integration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='mortgage_calc'),
        'USER': env('DB_USER', default='admin'),
        'PASSWORD': env('DB_PASSWORD', default='password'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:3000', 'http://localhost:80']
)
CORS_ALLOW_CREDENTIALS = True

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_REFRESH_TOKEN_LIFETIME', default=1440)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Mortgage Calculator API',
    'DESCRIPTION': 'API for mortgage calculations with intelligent tax data scraping',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Celery Configuration
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),
    }
}

# LLM Configuration
LLM_PROVIDER = env('LLM_PROVIDER', default='openai')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
LLM_MODEL = env('LLM_MODEL', default='gpt-4-turbo-preview')

# OCR Configuration
OCR_PROVIDER = env('OCR_PROVIDER', default='tesseract')
DEEPSEEK_OCR_API_KEY = env('DEEPSEEK_OCR_API_KEY', default='')
TESSERACT_PATH = env('TESSERACT_PATH', default='/usr/bin/tesseract')

# Web Search Configuration
WEB_SEARCH_PROVIDER = env('WEB_SEARCH_PROVIDER', default='serpapi')
SERP_API_KEY = env('SERP_API_KEY', default='')
BRAVE_SEARCH_API_KEY = env('BRAVE_SEARCH_API_KEY', default='')

# Scraper Configuration
SCRAPER_SERVICE_URL = env('SCRAPER_SERVICE_URL', default='http://localhost:8001')
SCRAPER_CACHE_EXPIRY_DAYS = env.int('SCRAPER_CACHE_EXPIRY_DAYS', default=30)
SCRAPER_MAX_RETRIES = env.int('SCRAPER_MAX_RETRIES', default=3)
SCRAPER_TIMEOUT = env.int('SCRAPER_TIMEOUT', default=300)

# File Upload Settings
MAX_UPLOAD_SIZE = env.int('MAX_UPLOAD_SIZE', default=10485760)  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': env('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'scraper_integration': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Sentry Configuration (optional)
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True
    )

# Feature Flags
ENABLE_AUTO_RESCRAPE = env.bool('ENABLE_AUTO_RESCRAPE', default=True)
ENABLE_OCR_PROCESSING = env.bool('ENABLE_OCR_PROCESSING', default=True)
ENABLE_DOCUMENT_UPLOAD = env.bool('ENABLE_DOCUMENT_UPLOAD', default=True)

# Document Storage Configuration
DOCUMENT_STORAGE_BACKEND = env('DOCUMENT_STORAGE_BACKEND', default='local')  # 'local' or 's3'

# AWS S3 Configuration (for production document storage)
if DOCUMENT_STORAGE_BACKEND == 's3':
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='mortgage-documents')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    # Use django-storages for S3
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Virus Scanning Configuration
ENABLE_VIRUS_SCAN = env.bool('ENABLE_VIRUS_SCAN', default=not DEBUG)  # Enabled in production
CLAMAV_SOCKET_PATH = env('CLAMAV_SOCKET_PATH', default='/var/run/clamav/clamd.ctl')
ALLOWED_DOCUMENT_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/tiff',
    'image/gif',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
]

# OCR Service Configuration
OCR_SERVICE_URL = env('OCR_SERVICE_URL', default='http://localhost:8003')

# Security & Compliance Configuration
# Field-level encryption key for PII (SSN, DOB, account numbers)
# IMPORTANT: In production, store this in a secure key management system (AWS KMS, HashiCorp Vault)
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY', default=SECRET_KEY[:32].encode('utf-8'))

# PII Masking Configuration
MASK_SSN_IN_LOGS = env.bool('MASK_SSN_IN_LOGS', default=True)
MASK_ACCOUNT_NUMBERS = env.bool('MASK_ACCOUNT_NUMBERS', default=True)

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# =============================================================================
# Phase 2: Income Calculation Service Configuration
# =============================================================================

# Income Calculation Rules - Configurable via environment variables
# These rules control income qualification logic per underwriting guidelines

# Exclude income sources with fewer than 10 payment history entries
# Rationale: Insufficient payment history indicates unstable/new income source
INCOME_EXCLUDE_LESS_THAN_10_PAYMENTS = env.bool(
    'INCOME_EXCLUDE_LESS_THAN_10_PAYMENTS',
    default=False
)

# Exclude cosigned debt from DTI calculations
# Rationale: Borrower may not be responsible for full payment if cosigned
INCOME_EXCLUDE_COSIGNED_DEBT = env.bool(
    'INCOME_EXCLUDE_COSIGNED_DEBT',
    default=False
)

# Variable income averaging period (in months)
# Standard: 24 months (2 years) for overtime, bonus, commission
INCOME_VARIABLE_AVERAGE_MONTHS = env.int(
    'INCOME_VARIABLE_AVERAGE_MONTHS',
    default=24
)

# Schedule C income averaging period (in months)
# Standard: 24 months (2 years) for self-employment income
INCOME_SCHEDULE_C_AVERAGE_MONTHS = env.int(
    'INCOME_SCHEDULE_C_AVERAGE_MONTHS',
    default=24
)

# Minimum years of self-employment history required
INCOME_SCHEDULE_C_MIN_YEARS = env.int(
    'INCOME_SCHEDULE_C_MIN_YEARS',
    default=2
)

# =============================================================================
# Phase 3: Pricing Adapter Configuration (Scenario Desk)
# =============================================================================

# Pricing API Configuration
# Provider: 'mock', 'optimal_blue', 'encompass', 'custom'
PRICING_PROVIDER = env('PRICING_PROVIDER', default='mock')
PRICING_API_KEY = env('PRICING_API_KEY', default='')
PRICING_API_URL = env('PRICING_API_URL', default='')
PRICING_API_TIMEOUT = env.int('PRICING_API_TIMEOUT', default=30)  # seconds

# Enable pricing audit logging
PRICING_ENABLE_AUDIT_LOG = env.bool('PRICING_ENABLE_AUDIT_LOG', default=True)

# Cache pricing results (in seconds, 0 = disabled)
PRICING_CACHE_TTL = env.int('PRICING_CACHE_TTL', default=300)  # 5 minutes
