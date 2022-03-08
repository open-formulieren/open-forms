import json
import os

# Django-hijack (and Django-hijack-admin)
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

import sentry_sdk
from celery.schedules import crontab
from corsheaders.defaults import default_headers as default_cors_headers

from .utils import Filesize, config, get_sentry_integrations

# Build paths inside the project, so further paths can be defined relative to
# the code root.
DJANGO_PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir)
)
BASE_DIR = os.path.abspath(
    os.path.join(DJANGO_PROJECT_DIR, os.path.pardir, os.path.pardir)
)

#
# Core Django settings
#
# SITE_ID = config("SITE_ID", default=1)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

# NEVER run with DEBUG=True in production-like environments
DEBUG = config("DEBUG", default=False)

# = domains we're running on
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", split=True)

IS_HTTPS = config("IS_HTTPS", default=not DEBUG)

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "nl"
LANGUAGES = [
    ("en", _("English")),
    ("nl", _("Dutch")),
]

TIME_ZONE = "Europe/Amsterdam"  # note: this *may* affect the output of DRF datetimes

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

#
# DATABASE and CACHING setup
#
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": config("DB_NAME", "openforms"),
        "USER": config("DB_USER", "openforms"),
        "PASSWORD": config("DB_PASSWORD", "openforms"),
        "HOST": config("DB_HOST", "localhost"),
        "PORT": config("DB_PORT", 5432),
    }
}

# keep the current schema for now and deal with migrating to BigAutoField later, see
# https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_DEFAULT', 'localhost:6379/0')}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
    "axes": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_AXES', 'localhost:6379/0')}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
    "oidc": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_OIDC', 'localhost:6379/0')}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
    "portalocker": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('CACHE_PORTALOCKER', 'localhost:6379/0')}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": False,
        },
    },
}

#
# APPLICATIONS enabled for this project
#

INSTALLED_APPS = [
    # Note: contenttypes should be first, see Django ticket #10827
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    # NOTE: If enabled, at least one Site object is required and
    # uncomment SITE_ID above.
    # "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Admin auth
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    # Optional applications.
    "ordered_model",
    "django_admin_index",
    "django.contrib.admin",
    # 'django.contrib.admindocs',
    # 'django.contrib.humanize',
    # 'django.contrib.sitemaps',
    # External applications.
    "axes",
    "capture_tag",
    "cookie_consent",
    "corsheaders",
    "django_better_admin_arrayfield",
    "django_yubin",
    "hijack",
    "hijack.contrib.admin",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "drf_polymorphic",
    "digid_eherkenning",
    "solo",
    "timeline_logger",
    "tinymce",
    "privates",
    "zgw_consumers",
    "stuf",
    "stuf.stuf_bg",
    "stuf.stuf_zds",
    "mozilla_django_oidc",
    "mozilla_django_oidc_db",
    "django_filters",
    "csp",
    "cspreports",
    "csp_post_processor",
    "django_camunda",
    # Project applications.
    "openforms.accounts",
    "openforms.appointments.apps.AppointmentsAppConfig",
    "openforms.appointments.contrib.jcc.apps.JccPlugin",
    "openforms.appointments.contrib.qmatic.apps.QmaticPlugin",
    "openforms.config",
    "openforms.emails",
    "openforms.formio",
    "openforms.formio.formatters.apps.FormIOFormattersApp",
    "openforms.forms",
    "openforms.multidomain",
    "openforms.products",
    "openforms.ui",
    "openforms.submissions",
    "openforms.logging.apps.LoggingAppConfig",
    "openforms.contrib.brp",
    "openforms.contrib.kvk",
    "openforms.contrib.bag.apps.BAGConfig",
    "openforms.contrib.microsoft.apps.MicrosoftApp",
    "openforms.registrations",
    "openforms.registrations.contrib.demo",
    "openforms.registrations.contrib.zgw_apis",
    "openforms.registrations.contrib.email",
    "openforms.registrations.contrib.stuf_zds",
    "openforms.registrations.contrib.objects_api",
    "openforms.registrations.contrib.microsoft_graph.apps.MicrosoftGraphApp",
    "openforms.registrations.contrib.camunda.apps.CamundaApp",
    "openforms.prefill",
    "openforms.prefill.contrib.demo.apps.DemoApp",
    "openforms.prefill.contrib.kvk.apps.KVKPrefillApp",
    "openforms.prefill.contrib.stufbg.apps.StufBgApp",
    "openforms.prefill.contrib.haalcentraal.apps.HaalCentraalApp",
    "openforms.authentication",
    "openforms.authentication.contrib.demo.apps.DemoApp",
    "openforms.authentication.contrib.outage.apps.DemoOutageApp",
    "openforms.authentication.contrib.digid_mock.apps.DigidMockApp",
    "openforms.authentication.contrib.digid.apps.DigidApp",
    "openforms.authentication.contrib.eherkenning.apps.EHerkenningApp",
    "openforms.payments.apps.PaymentsConfig",
    "openforms.payments.contrib.demo.apps.DemoApp",
    "openforms.payments.contrib.ogone.apps.OgoneApp",
    "openforms.data_removal",
    "openforms.utils",
    "openforms.custom_field_types",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "openforms.middleware.SameSiteNoneCookieMiddlware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 'django.middleware.locale.LocaleMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "openforms.middleware.SessionTimeoutMiddleware",
    "mozilla_django_oidc_db.middleware.SessionRefresh",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
    "csp.contrib.rate_limiting.RateLimitedCSPMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "openforms.urls"

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(DJANGO_PROJECT_DIR, "templates"),
        ],
        "APP_DIRS": False,  # conflicts with explicity specifying the loaders
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "openforms.forms.context_processors.sdk_urls",
                "openforms.utils.context_processors.settings",
            ],
            "loaders": TEMPLATE_LOADERS,
            "builtins": [
                "openforms.emails.templatetags.appointments",
                "openforms.emails.templatetags.form_summary",
                "openforms.emails.templatetags.payment",
                "openforms.emails.templatetags.products",
                "openforms.config.templatetags.privacy_policy",
            ],
        },
    },
]

WSGI_APPLICATION = "openforms.wsgi.application"

# Translations
LOCALE_PATHS = (
    os.path.join(DJANGO_PROJECT_DIR, "conf", "locale"),
    os.path.join(DJANGO_PROJECT_DIR, "conf", "locale_extensions"),
)

#
# SERVING of static and media files
#

STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Additional locations of static files
STATICFILES_DIRS = [
    os.path.join(DJANGO_PROJECT_DIR, "static"),
    # font-awesome fonts from formio
    (
        "bundles/fonts",
        os.path.join(BASE_DIR, "node_modules", "formiojs", "dist", "fonts"),
    ),
]

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

MEDIA_URL = "/media/"

PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, "private_media")

PRIVATE_MEDIA_URL = "/private-media/"

FILE_UPLOAD_PERMISSIONS = 0o644

SENDFILE_BACKEND = "django_sendfile.backends.nginx"
SENDFILE_ROOT = PRIVATE_MEDIA_ROOT
SENDFILE_URL = PRIVATE_MEDIA_URL

#
# Sending EMAIL
#
EMAIL_BACKEND = "django_yubin.smtp_queue.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config(
    "EMAIL_PORT", default=25
)  # disabled on Google Cloud, use 487 instead
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False)
EMAIL_TIMEOUT = 10

DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", "openforms@example.com")

#
# LOGGING
#
LOG_STDOUT = config("LOG_STDOUT", default=False)

LOGGING_DIR = os.path.join(BASE_DIR, "log")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(process)d %(thread)d  %(message)s"
        },
        "timestamped": {"format": "%(asctime)s %(levelname)s %(name)s  %(message)s"},
        "simple": {"format": "%(levelname)s  %(message)s"},
        "performance": {
            "format": "%(asctime)s %(process)d | %(thread)d | %(message)s",
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "timestamped",
        },
        "django": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGGING_DIR, "django.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
        },
        "project": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGGING_DIR, "openforms.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
        },
        "performance": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGGING_DIR, "performance.log"),
            "formatter": "performance",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
        },
    },
    "loggers": {
        "openforms": {
            "handlers": ["project"] if not LOG_STDOUT else ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "stuf": {
            "handlers": ["project"] if not LOG_STDOUT else ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["django"] if not LOG_STDOUT else ["console"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.template": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "mozilla_django_oidc": {
            "handlers": ["project"] if not LOG_STDOUT else ["console"],
            "level": "DEBUG",
        },
    },
}

#
# AUTH settings - user accounts, passwords, backends...
#
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Allow logging in with both username+password and email+password
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesBackend",
    "openforms.accounts.backends.UserModelEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend",
]

SESSION_COOKIE_NAME = "openforms_sessionid"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_EXPIRE_AT_BROWSER_CLOSE = config(
    "SESSION_EXPIRE_AT_BROWSER_CLOSE", default=False
)

LOGIN_URL = reverse_lazy("admin:login")
LOGIN_REDIRECT_URL = reverse_lazy("admin:index")
LOGOUT_REDIRECT_URL = reverse_lazy("admin:index")

#
# SECURITY settings
#
SESSION_COOKIE_SECURE = IS_HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = (
    None  # from Lax -> None to enable the SDK to send CORS requests
)

CSRF_COOKIE_SECURE = IS_HTTPS

X_FRAME_OPTIONS = "DENY"

#
# FIXTURES
#

FIXTURE_DIRS = (os.path.join(DJANGO_PROJECT_DIR, "fixtures"),)

#
# Custom settings
#
PROJECT_NAME = "Open Formulieren"
ENVIRONMENT = config("ENVIRONMENT", "")
SHOW_ALERT = True

if "GIT_SHA" in os.environ:
    GIT_SHA = config("GIT_SHA", "")
# in docker (build) context, there is no .git directory
elif os.path.exists(os.path.join(BASE_DIR, ".git")):
    try:
        import git
    except ImportError:
        GIT_SHA = None
    else:
        repo = git.Repo(search_parent_directories=True)
        GIT_SHA = repo.head.object.hexsha
else:
    GIT_SHA = None

RELEASE = config("RELEASE", GIT_SHA)

with open(os.path.join(BASE_DIR, ".sdk-release"), "r") as sdk_release_file:
    sdk_release_default = sdk_release_file.read().strip()

SDK_RELEASE = config("SDK_RELEASE", default=sdk_release_default)

BASE_URL = config("BASE_URL", "https://open-forms.test.maykin.opengem.nl")

# Submission download: how long-lived should the one-time URL be:
SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS = config(
    "SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS", default=1
)
TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS = config(
    "TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS", default=2
)

# a custom default timeout for the requests library, added via monkeypatch in
# :mod:`openforms.setup`. Value is in seconds.
DEFAULT_TIMEOUT_REQUESTS = config("DEFAULT_TIMEOUT_REQUESTS", default=10.0)

MAX_FILE_UPLOAD_SIZE = config("MAX_FILE_UPLOAD_SIZE", default="50M", cast=Filesize())

##############################
#                            #
# 3RD PARTY LIBRARY SETTINGS #
#                            #
##############################

#
# Django-Admin-Index
#
ADMIN_INDEX_AUTO_CREATE_APP_GROUP = False

ADMIN_INDEX_DISPLAY_DROP_DOWN_MENU_CONDITION_FUNCTION = (
    "openforms.utils.django_two_factor_auth.should_display_dropdown_menu"
)

#
# DJANGO-AXES (4.0+)
#
AXES_CACHE = "axes"  # refers to CACHES setting
# The number of login attempts allowed before a record is created for the
# failed logins. Default: 3
AXES_FAILURE_LIMIT = 10
# If set, defines a period of inactivity after which old failed login attempts
# will be forgotten. Can be set to a python timedelta object or an integer. If
# an integer, will be interpreted as a number of hours. Default: None
AXES_COOLOFF_TIME = 1
# If True only locks based on user id and never locks by IP if attempts limit
# exceed, otherwise utilize the existing IP and user locking logic Default:
# False
AXES_ONLY_USER_FAILURES = True
# If set, specifies a template to render when a user is locked out. Template
# receives cooloff_time and failure_limit as context variables. Default: None
AXES_LOCKOUT_TEMPLATE = "account_blocked.html"
AXES_USE_USER_AGENT = True  # Default: False
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # Default: False
AXES_BEHIND_REVERSE_PROXY = IS_HTTPS

# The default meta precedence order
IPWARE_META_PRECEDENCE_ORDER = (
    "HTTP_X_FORWARDED_FOR",
    "X_FORWARDED_FOR",  # <client>, <proxy1>, <proxy2>
    "HTTP_CLIENT_IP",
    "HTTP_X_REAL_IP",
    "HTTP_X_FORWARDED",
    "HTTP_X_CLUSTER_CLIENT_IP",
    "HTTP_FORWARDED_FOR",
    "HTTP_FORWARDED",
    "HTTP_VIA",
    "REMOTE_ADDR",
)

#
# Maykin fork of DJANGO-TWO-FACTOR-AUTH
#
TWO_FACTOR_FORCE_OTP_ADMIN = config("TWO_FACTOR_FORCE_OTP_ADMIN", default=not DEBUG)
TWO_FACTOR_PATCH_ADMIN = config("TWO_FACTOR_PATCH_ADMIN", default=True)

#
# CELERY - async task queue
#
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Add a 30 minutes timeout to all Celery tasks.
CELERY_TASK_SOFT_TIME_LIMIT = 30 * 60

CELERY_BEAT_SCHEDULE = {
    "clear-session-store": {
        "task": "openforms.utils.tasks.clear_session_store",
        # https://docs.celeryproject.org/en/v4.4.7/userguide/periodic-tasks.html#crontab-schedules
        "schedule": crontab(minute=0, hour=0),
    },
    "send-emails": {
        "task": "openforms.utils.tasks.send_emails",
        "schedule": config("BEAT_SEND_EMAIL_INTERVAL", default=20),  # every 20 seconds
    },
    "retry-submissions-processing": {
        "task": "openforms.submissions.tasks.retry_processing_submissions",
        "schedule": config("RETRY_SUBMISSIONS_INTERVAL", default=60 * 5),
    },
    "delete-submissions": {
        "task": "openforms.data_removal.tasks.delete_submissions",
        "schedule": crontab(minute=0, hour=1),
    },
    "make-sensitive-data-anonymous": {
        "task": "openforms.data_removal.tasks.make_sensitive_data_anonymous",
        "schedule": crontab(minute=0, hour=2),
    },
    "cleanup-unclaimed-temp-files": {
        "task": "openforms.submissions.tasks.user_uploads.cleanup_unclaimed_temporary_files",
        "schedule": crontab(minute=30, hour=3),
    },
    "cleanup_on_completion_results": {
        "task": "openforms.submissions.tasks.cleanup.cleanup_on_completion_results",
        "schedule": crontab(minute=45, hour=4),
    },
    "cleanup_csp_reports": {
        "task": "openforms.utils.tasks.cleanup_csp_reports",
        "schedule": crontab(hour=4),
    },
}

RETRY_SUBMISSIONS_TIME_LIMIT = config(
    "RETRY_SUBMISSIONS_TIME_LIMIT", default=48  # hours
)

# Only ACK when the task has been executed. This prevents tasks from getting lost, with
# the drawback that tasks should be idempotent (if they execute partially, the mutations
# executed will be executed again!)
CELERY_TASK_ACKS_LATE = True

# ensure that no tasks are scheduled to a worker that may be running a very long-running
# operation, leading to idle workers and backed-up workers. The `-O fair` option
# *should* have the same effect...
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

#
# DJANGO-CORS-MIDDLEWARE
#
# CORS requests are required if the SDK is used in another domain. When developing
# on the SDK for example, set `CORS_ALLOWED_ORIGINS=http://localhost:3000` in your
# Open Forms .env
# NOTE these are also used by the authentication plugins to verify redirects
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", split=True, default=[])
CORS_ALLOWED_ORIGIN_REGEXES = config(
    "CORS_ALLOWED_ORIGIN_REGEXES", split=True, default=[]
)
# Authorization is included in default_cors_headers
CORS_ALLOW_HEADERS = list(default_cors_headers) + config(
    "CORS_EXTRA_ALLOW_HEADERS", split=True, default=[]
)
CORS_EXPOSE_HEADERS = ["X-Session-Expires-In"]
CORS_ALLOW_CREDENTIALS = True  # required to send cross domain cookies

#
# SENTRY - error monitoring
#
SENTRY_DSN = config("SENTRY_DSN", "")

if SENTRY_DSN:
    SENTRY_CONFIG = {
        "dsn": SENTRY_DSN,
        "release": RELEASE,
        "environment": ENVIRONMENT,
    }

    sentry_sdk.init(
        **SENTRY_CONFIG, integrations=get_sentry_integrations(), send_default_pii=True
    )

# Sentry for the Open-Forms SDK
SDK_SENTRY_DSN = config("SDK_SENTRY_DSN", "")
SDK_SENTRY_ENVIRONMENT = config("SDK_SENTRY_ENVIRONMENT", ENVIRONMENT)

#
# Elastic APM
#
ELASTIC_APM_SERVER_URL = config("ELASTIC_APM_SERVER_URL", None)
ELASTIC_APM = {
    "SERVICE_NAME": f"Open Forms - {ENVIRONMENT}",
    "SECRET_TOKEN": config("ELASTIC_APM_SECRET_TOKEN", "default"),
    "SERVER_URL": ELASTIC_APM_SERVER_URL,
}
if not ELASTIC_APM_SERVER_URL:
    ELASTIC_APM["ENABLED"] = False
    ELASTIC_APM["SERVER_URL"] = "http://localhost:8200"
else:
    MIDDLEWARE = ["elasticapm.contrib.django.middleware.TracingMiddleware"] + MIDDLEWARE
    INSTALLED_APPS = INSTALLED_APPS + [
        "elasticapm.contrib.django",
    ]

#
# DJANGO REST FRAMEWORK
#
ENABLE_THROTTLING = config("ENABLE_THROTTLING", default=True)

throttle_rate_anon = (
    config("THROTTLE_RATE_ANON", default="2500/hour") if ENABLE_THROTTLING else None
)
throttle_rate_user = (
    config("THROTTLE_RATE_USER", default="15000/hour") if ENABLE_THROTTLING else None
)
throttle_rate_polling = (
    config("THROTTLE_RATE_POLLING", default="50000/hour") if ENABLE_THROTTLING else None
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        # used by regular throttle classes
        "anon": throttle_rate_anon,
        "user": throttle_rate_user,
        # used by custom throttle class
        "polling": throttle_rate_polling,
    },
    # required to get the right IP addres for throttling depending on the amount of
    # reverse proxies (X-Forwarded-For).
    "NUM_PROXIES": config(
        "NUM_PROXIES",
        default=1,
        cast=lambda val: int(val) if val is not None else None,
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_SCHEMA_CLASS": "openforms.api.schema.AutoSchema",
    "EXCEPTION_HANDLER": "openforms.api.views.exception_handler",
}

#
# SPECTACULAR - OpenAPI schema generation
#

_DESCRIPTION = """
Open Forms provides an API to manage multi-page or multi-step forms.

It supports listing and retrieving forms, which are made up of form steps. Each form
step has a form definition driven by [FormIO.js](https://github.com/formio/formio.js/)
definitions.

Submissions of forms are supported, where each form step can be submitted individually.
Complete submissions are sent to the configured backend, which is a pluggable system
to hook into [Open Zaak](https://openzaak.org), [Camunda](https://camunda.com/) or
other systems.

Open Forms fits in the [Common Ground](https://commonground.nl) vision and architecture,
and it plays nice with other available components.
"""

API_VERSION = "1.0.0"

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "TITLE": "Open Forms API",
    "DESCRIPTION": _DESCRIPTION,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
        "openforms.api.drf_spectacular.hooks.add_middleware_headers",
    ],
    "TOS": None,
    # Optional: MAY contain "name", "url", "email"
    "CONTACT": {
        "url": "https://github.com/maykinmedia/open-forms",
        "email": "support@maykinmedia.nl",
    },
    # Optional: MUST contain "name", MAY contain URL
    "LICENSE": {
        "name": "UNLICENSED",
    },
    "VERSION": API_VERSION,
    # Tags defined in the global scope
    "TAGS": [],
    # Optional: MUST contain 'url', may contain "description"
    "EXTERNAL_DOCS": {
        "description": "Functional and technical documentation",
        "url": "https://open-forms.readthedocs.io/",
    },
    "ENUM_NAME_OVERRIDES": {
        "IncompleteSubmissionsRemovalMethodEnum": "openforms.data_removal.constants.RemovalMethods",
    },
}

#
# ZGW Consumers
#
ZGW_CONSUMERS_CLIENT_CLASS = "zgw_consumers.client.ZGWClient"
ZGW_CONSUMERS_TEST_SCHEMA_DIRS = [
    os.path.join(BASE_DIR, "src/openforms/registrations/contrib/zgw_apis/tests/files"),
    os.path.join(
        BASE_DIR, "src/openforms/registrations/contrib/objects_api/tests/files"
    ),
    os.path.join(BASE_DIR, "src/openforms/prefill/contrib/haalcentraal/tests/files"),
    os.path.join(BASE_DIR, "src/openforms/contrib/kvk/tests/files"),
    os.path.join(BASE_DIR, "src/openforms/contrib/bag/tests/files"),
]

#
# Django Solo
#
SOLO_CACHE = "default"
SOLO_CACHE_TIMEOUT = 60 * 5  # 5 minutes

#
# Self-Certifi
#
SELF_CERTIFI_DIR = config(
    "SELF_CERTIFI_DIR", os.path.join(BASE_DIR, "certifi_ca_bundle")
)

#
# Django Cookie-Consent
#
COOKIE_CONSENT_NAME = "cookie_consent"

#
# DIGID
#

DIGID_METADATA = config("DIGID_METADATA", "")
SSL_CERTIFICATE_PATH = config("SSL_CERTIFICATE_PATH", "")
SSL_KEY_PATH = config("SSL_KEY_PATH", "")
DIGID_SERVICE_ENTITY_ID = config(
    "DIGID_SERVICE_ENTITY_ID", "https://was-preprod1.digid.nl/saml/idp/metadata"
)
DIGID_WANT_ASSERTIONS_SIGNED = config("DIGID_WANT_ASSERTIONS_SIGNED", default=True)

DIGID = {
    "base_url": BASE_URL,
    "entity_id": BASE_URL,
    # This is the metadata of the **Identity provider** NOT our own!
    "metadata_file": DIGID_METADATA,
    # SSL/TLS key
    "key_file": SSL_KEY_PATH,
    "cert_file": SSL_CERTIFICATE_PATH,
    "service_entity_id": DIGID_SERVICE_ENTITY_ID,
    "attribute_consuming_service_index": "1",
    "requested_attributes": ["bsn"],
    # Logius can sign the assertions (True) but others sign the entire response
    # (False).
    "want_assertions_signed": DIGID_WANT_ASSERTIONS_SIGNED,
}

#
# E-HERKENNING / eIDAS
#

EHERKENNING_METADATA = config("EHERKENNING_METADATA", "")
EHERKENNING_SERVICE_ENTITY_ID = config("EHERKENNING_SERVICE_ENTITY_ID", "")
EHERKENNING_ENTITY_ID = config("EHERKENNING_ENTITY_ID", "")
EHERKENNING_LOA = config("EHERKENNING_LOA", "urn:etoegang:core:assurance-class:loa3")
EHERKENNING_OIN = config("EHERKENNING_OIN", "")
EHERKENNING_WANT_ASSERTIONS_SIGNED = config("EHERKENNING_WANT_ASSERTIONS_SIGNED", True)
EHERKENNING_WANT_ASSERTIONS_ENCRYPTED = config(
    "EHERKENNING_WANT_ASSERTIONS_ENCRYPTED", False
)
EHERKENNING_SIGNATURE_ALGORITHM = config(
    "EHERKENNING_SIGNATURE_ALGORITHM",
    "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
)

EHERKENNING_SERVICE_INDEX = config("EHERKENNING_SERVICE_INDEX", "1")
EHERKENNING_SERVICE_UUID = config("EHERKENNING_SERVICE_UUID", "")
EHERKENNING_SERVICE_INSTANCE_UUID = config("EHERKENNING_SERVICE_INSTANCE_UUID", "")

EIDAS_SERVICE_INDEX = config("EIDAS_SERVICE_INDEX", "2")
EIDAS_SERVICE_UUID = config("EIDAS_SERVICE_UUID", "")
EIDAS_SERVICE_INSTANCE_UUID = config("EIDAS_SERVICE_INSTANCE_UUID", "")

EHERKENNING = {
    "want_assertions_signed": EHERKENNING_WANT_ASSERTIONS_SIGNED,
    "want_assertions_encrypted": EHERKENNING_WANT_ASSERTIONS_ENCRYPTED,
    "signature_algorithm": EHERKENNING_SIGNATURE_ALGORITHM,
    "metadata_file": EHERKENNING_METADATA,
    "key_file": SSL_KEY_PATH,
    "cert_file": SSL_CERTIFICATE_PATH,
    "base_url": BASE_URL,
    "service_entity_id": EHERKENNING_SERVICE_ENTITY_ID,
    "entity_id": EHERKENNING_ENTITY_ID,
    "oin": EHERKENNING_OIN,
    "services": [
        {
            "attribute_consuming_service_index": EHERKENNING_SERVICE_INDEX,
            "service_loa": EHERKENNING_LOA,
            "service_uuid": EHERKENNING_SERVICE_UUID,
            "service_instance_uuid": EHERKENNING_SERVICE_INSTANCE_UUID,
            "service_url": BASE_URL,
            # Either require and return RSIN and KVKNr (set 1) or require only KvKnr (set 2). The
            # latter is needed for 'eenmanszaak'
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:RSIN"},
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
                {"set_number": "2", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
        },
    ],
}

if EIDAS_SERVICE_INDEX:
    EHERKENNING["services"].append(
        {
            "attribute_consuming_service_index": EIDAS_SERVICE_INDEX,
            "service_loa": EHERKENNING_LOA,
            "service_uuid": EIDAS_SERVICE_UUID,
            "service_instance_uuid": EIDAS_SERVICE_INSTANCE_UUID,
            "service_url": BASE_URL,
            "entity_concerned_types_allowed": [
                {"set_number": "1", "name": "urn:etoegang:1.9:EntityConcernedID:KvKnr"},
            ],
            "requested_attributes": [],
            "language": "nl",
            "classifiers": ["eIDAS-inbound"],
        }
    )

#
# Location Client
#
OPENFORMS_LOCATION_CLIENT = config(
    "OPENFORMS_LOCATION_CLIENT", "openforms.contrib.bag.client.BAGClient"
)

#
# Mozilla Django OIDC DB settings
#
OIDC_AUTHENTICATE_CLASS = "mozilla_django_oidc_db.views.OIDCAuthenticationRequestView"
OIDC_CALLBACK_CLASS = "openforms.accounts.oidc.views.OIDCCallbackView"
MOZILLA_DJANGO_OIDC_DB_CACHE = "oidc"
MOZILLA_DJANGO_OIDC_DB_CACHE_TIMEOUT = 5 * 60

#
# Email / payment
#
PAYMENT_CONFIRMATION_EMAIL_TIMEOUT = 60 * 15

#
# Django CSP settings
#
# explanation of directives: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy
# and how to specify them: https://django-csp.readthedocs.io/en/latest/configuration.html
#
# NOTE: make sure values are a tuple or list, and to quote special values like 'self'

# ideally we'd use BASE_URI but it'd have to be lazy or cause issues
CSP_DEFAULT_SRC = [
    "'self'",
] + config("CSP_EXTRA_DEFAULT_SRC", default=[], split=True)

# * service.pdok.nl serves the tiles for the Leaflet maps (PNGs) and must be whitelisted
# * the data: URIs are used by Leaflet (invisible pixel for memory management/image unloading)
#   and the signature component which saves the image drawn on the canvas as data: URI
CSP_IMG_SRC = (
    CSP_DEFAULT_SRC
    + ["data:", "https://service.pdok.nl/"]
    + config("CSP_EXTRA_IMG_SRC", default=[], split=True)
)

# we must include this explicitly, otherwise the style-src only includes the nonce because
# of CSP_INCLUDE_NONCE_IN
CSP_STYLE_SRC = CSP_DEFAULT_SRC
CSP_SCRIPT_SRC = CSP_DEFAULT_SRC

# firefox does not get the nonce from default-src, see
# https://stackoverflow.com/a/63376012
CSP_INCLUDE_NONCE_IN = ["style-src", "script-src"]

# directives that don't fallback to default-src
CSP_BASE_URI = ["'self'"]

# Frame directives do not fall back to default-src
CSP_FRAME_ANCESTORS = ["'self'"]
CSP_FRAME_SRC = ["'self'"]
# CSP_NAVIGATE_TO = ["'self'"]  # this will break all outgoing links etc  # too much & tricky, see note on MDN
# CSP_FORM_ACTION = ["'self'"]  # forms, possibly problematic with payments
# CSP_SANDBOX # too much

CSP_UPGRADE_INSECURE_REQUESTS = False  # TODO enable on production?

CSP_EXCLUDE_URL_PREFIXES = (
    # ReDoc/Swagger pull in external sources, so don't enforce CSP on API endpoints/documentation.
    "/api/",
    # FIXME: Admin pulls in bootstrap from CDN & has inline styles/scripts probably
    "/admin/",
)

# note these are outdated/deprecated django-csp options
# CSP_BLOCK_ALL_MIXED_CONTENT
# CSP_PLUGIN_TYPES
# CSP_CHILD_SRC

# report to our own django-csp-reports
CSP_REPORT_ONLY = config("CSP_REPORT_ONLY", False)  # enforce by default
CSP_REPORT_URI = reverse_lazy("report_csp")

#
# Django CSP-report settings
#
CSP_REPORTS_SAVE = config("CSP_REPORTS_SAVE", False)  # save as model
CSP_REPORTS_LOG = config("CSP_REPORTS_LOG", True)  # logging
CSP_REPORTS_LOG_LEVEL = "warning"
CSP_REPORTS_EMAIL_ADMINS = False
CSP_REPORT_PERCENTAGE = config("CSP_REPORT_PERCENTAGE", 1.0)  # float between 0 and 1
CSP_REPORTS_FILTER_FUNCTION = "cspreports.filters.filter_browser_extensions"

#
# Tiny MCE default settings
#
with open(os.path.join(os.path.dirname(__file__), "tinymce_config.json")) as f:
    # NOTE django-tinymce will add locale/language settings automatically
    TINYMCE_DEFAULT_CONFIG = json.load(f)

#
# Django Hijack
#
HIJACK_INSERT_BEFORE = (
    '<div class="content">'  # note that this only applies to the admin
)

#
# Open Forms extensions
#

OPEN_FORMS_EXTENSIONS = config("OPEN_FORMS_EXTENSIONS", split=True, default=[])

if OPEN_FORMS_EXTENSIONS:
    INSTALLED_APPS += OPEN_FORMS_EXTENSIONS
