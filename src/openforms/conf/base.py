import os

# Django-hijack (and Django-hijack-admin)
from django.urls import reverse_lazy

import sentry_sdk
from corsheaders.defaults import default_headers as default_cors_headers

from .utils import config, get_sentry_integrations

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

LANGUAGE_CODE = "nl-nl"

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
    # 'django.contrib.sites',
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Optional applications.
    "ordered_model",
    "django_admin_index",
    "django.contrib.admin",
    # 'django.contrib.admindocs',
    # 'django.contrib.humanize',
    # 'django.contrib.sitemaps',
    # External applications.
    "axes",
    "corsheaders",
    "hijack",
    "hijack_admin",
    "compat",  # Part of hijack
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "digid_eherkenning",
    "solo",
    "reversion",
    "zgw_consumers",
    # Project applications.
    "openforms.accounts",
    "openforms.forms",
    "openforms.products",
    "openforms.ui",
    "openforms.utils",
    "openforms.submissions",
    "openforms.contrib.brp",
    "openforms.registrations.contrib.demo",
    "openforms.registrations.contrib.zgw_rest",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 'django.middleware.locale.LocaleMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
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
            os.path.join(BASE_DIR, "src"),
        ],
        "APP_DIRS": False,  # conflicts with explicity specifying the loaders
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "openforms.utils.context_processors.settings",
            ],
            "loaders": TEMPLATE_LOADERS,
        },
    },
]

WSGI_APPLICATION = "openforms.wsgi.application"

# Translations
LOCALE_PATHS = (os.path.join(DJANGO_PROJECT_DIR, "conf", "locale"),)

#
# SERVING of static and media files
#

STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Additional locations of static files
STATICFILES_DIRS = [
    os.path.join(DJANGO_PROJECT_DIR, "static"),
    os.path.join(BASE_DIR, "src", "spa", "build", "static"),
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

FILE_UPLOAD_PERMISSIONS = 0o644

#
# Sending EMAIL
#
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
            "level": "INFO",
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
]

SESSION_COOKIE_NAME = "openforms_sessionid"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

LOGIN_URL = reverse_lazy("admin:login")
LOGIN_REDIRECT_URL = reverse_lazy("admin:index")

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

RELEASE = config("VERSION_TAG", GIT_SHA)

##############################
#                            #
# 3RD PARTY LIBRARY SETTINGS #
#                            #
##############################

#
# Django-Admin-Index
#
ADMIN_INDEX_AUTO_CREATE_APP_GROUP = False

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
# DJANGO-HIJACK
#
HIJACK_LOGIN_REDIRECT_URL = "/"
HIJACK_LOGOUT_REDIRECT_URL = reverse_lazy("admin:accounts_user_changelist")
HIJACK_REGISTER_ADMIN = False
# This is a CSRF-security risk.
# See: http://django-hijack.readthedocs.io/en/latest/configuration/#allowing-get-method-for-hijack-views
HIJACK_ALLOW_GET_REQUESTS = True

#
# DJANGO-CORS-MIDDLEWARE
#
# CORS requests are required if the SDK is used in another domain. When developing
# on the SDK for example, set `CORS_ALLOWED_ORIGINS=http://localhost:3000` in your
# Open Forms .env
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", split=True, default=[])
CORS_ALLOWED_ORIGIN_REGEXES = config(
    "CORS_ALLOWED_ORIGIN_REGEXES", split=True, default=[]
)
# Authorization is included in default_cors_headers
CORS_ALLOW_HEADERS = list(default_cors_headers) + config(
    "CORS_EXTRA_ALLOW_HEADERS", split=True, default=[]
)
CORS_EXPOSE_HEADERS = []
CORS_ALLOW_CREDENTIALS = True  # required to send cross domain cookies

#
# SENTRY - error monitoring
#
SENTRY_DSN = config("SENTRY_DSN", None)

if SENTRY_DSN:
    SENTRY_CONFIG = {
        "dsn": SENTRY_DSN,
        "release": RELEASE,
    }

    sentry_sdk.init(
        **SENTRY_CONFIG, integrations=get_sentry_integrations(), send_default_pii=True
    )

# Elastic APM

ELASTIC_APM = {
    "SERVICE_NAME": f"Open Forms {ENVIRONMENT}",
    "SECRET_TOKEN": config("ELASTIC_APM_SECRET_TOKEN", "default"),
    "SERVER_URL": config("ELASTIC_APM_SERVER_URL", "http://example.com"),
}

#
# DJANGO REST FRAMEWORK
#
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
    "DEFAULT_THROTTLE_RATES": {"anon": "200/day", "user": "1000/day"},
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_SCHEMA_CLASS": "openforms.api.schema.AutoSchema",
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

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "TITLE": "Open Forms API",
    "DESCRIPTION": _DESCRIPTION,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
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
    "VERSION": "1.0.0-alpha",
    # Tags defined in the global scope
    "TAGS": [],
    # Optional: MUST contain 'url', may contain "description"
    "EXTERNAL_DOCS": {
        "description": "Functional and technical documentation",
        "url": "https://open-forms.readthedocs.io/",
    },
}

#
# ZGW Consumers
#
ZGW_CONSUMERS_CLIENT_CLASS = "zgw_consumers.client.ZGWClient"
ZGW_CONSUMERS_TEST_SCHEMA_DIRS = [
    "openforms/registrations/contrib/zgw_rest/tests/files"
]
