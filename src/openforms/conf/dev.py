# ruff: noqa: F405
import os
import warnings

from maykin_common.config import config

os.environ.setdefault("DEBUG", "yes")
os.environ.setdefault("ALLOWED_HOSTS", "*")
os.environ.setdefault(
    "SECRET_KEY", "@r0w-0(&apjfde5fl6h23!vn)r1ldkp1c_d2#!$did4z5hun4a"
)
os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
os.environ.setdefault("VERSION_TAG", "dev")

os.environ.setdefault("DB_NAME", "openforms")
os.environ.setdefault("DB_USER", "openforms")
os.environ.setdefault("DB_PASSWORD", "openforms")

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("NUM_PROXIES", "0")

os.environ.setdefault(
    "EHERKENNING_PRIVACY_POLICY", "https://www.maykinmedia.nl/en/privacy/"
)
os.environ.setdefault("RELEASE", "dev")
os.environ.setdefault("SDK_RELEASE", "latest")
# otherwise the test suite is flaky due to logging config lookups to the DB in
# non-DB test cases
os.environ.setdefault("LOG_OUTGOING_REQUESTS", "no")
os.environ.setdefault("LOG_STDOUT", "1")
os.environ.setdefault("LOG_FORMAT_CONSOLE", "plain_console")
os.environ.setdefault("VCR_RECORD_MODE", "once")

os.environ.setdefault("SENDFILE_BACKEND", "django_sendfile.backends.development")

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("OTEL_EXPORTER_OTLP_METRICS_INSECURE", "true")

from .base import *  # noqa isort:skip

# Feel free to switch dev to sqlite3 for simple projects,
# os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")

#
# Standard Django settings.
#

SESSION_ENGINE = "django.contrib.sessions.backends.db"

LOGGING["loggers"].update(
    {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["json_file"],
            "level": "INFO",
            "propagate": False,
        },
        #
        # See: https://code.djangoproject.com/ticket/30554
        # Autoreload logs excessively, turn it down a bit.
        #
        "django.utils.autoreload": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "weasyprint": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    }
)

# in memory cache and django-axes don't get along.
# https://django-axes.readthedocs.io/en/latest/configuration.html#known-configuration-problems
CACHES.update(
    {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "oidc": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
)

#
# Library settings
#

ELASTIC_APM["DEBUG"] = config("DISABLE_APM_IN_DEV", default=True)

# Django debug toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
INTERNAL_IPS = ("127.0.0.1",)

# Django extensions
INSTALLED_APPS += ["django_extensions"]

# DRF - browsable API
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += [
    "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer"
]

# Django rosetta
ROSETTA_SHOW_AT_ADMIN_PANEL = True
INSTALLED_APPS += ["rosetta"]

#
# DJANGO-SILK
#
if config("PROFILE", default=False):
    INSTALLED_APPS += ["silk"]
    MIDDLEWARE = ["silk.middleware.SilkyMiddleware"] + MIDDLEWARE
    security_index = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    MIDDLEWARE.insert(security_index + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

#
# Disable CSP rate limit
#
DISABLE_CSP_RATELIMITING = config("DISABLE_CSP_RATELIMITING", default=False)
if DISABLE_CSP_RATELIMITING:
    MIDDLEWARE.remove("csp.contrib.rate_limiting.RateLimitedCSPMiddleware")

CSP_EXCLUDE_URL_PREFIXES += ("/dev/",)

# None of the authentication backends require two-factor authentication.
if config("DISABLE_2FA", default=True):  # pragma: no cover
    MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS = AUTHENTICATION_BACKENDS

# THOU SHALT NOT USE NAIVE DATETIMES
warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)

# Override settings with local settings.
try:
    from .local import *  # noqa
except ImportError:
    pass
