import os
import warnings

os.environ.setdefault("DEBUG", "yes")
os.environ.setdefault("ALLOWED_HOSTS", "*")
os.environ.setdefault(
    "SECRET_KEY", "@r0w-0(&apjfde5fl6h23!vn)r1ldkp1c_d2#!$did4z5hun4a"
)
os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("VERSION_TAG", "dev")

os.environ.setdefault("DB_NAME", "openforms"),
os.environ.setdefault("DB_USER", "openforms"),
os.environ.setdefault("DB_PASSWORD", "openforms"),

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("NUM_PROXIES", "0")

os.environ.setdefault(
    "EHERKENNING_PRIVACY_POLICY", "https://www.maykinmedia.nl/en/privacy/"
)
os.environ.setdefault("SDK_RELEASE", "latest")

from .base import *  # noqa isort:skip

# Feel free to switch dev to sqlite3 for simple projects,
# os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")

#
# Standard Django settings.
#

SESSION_ENGINE = "django.contrib.sessions.backends.db"

LOGGING["loggers"].update(
    {
        "openforms": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "stuf": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["django"],
            "level": "DEBUG",
            "propagate": False,
        },
        "performance": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        #
        # See: https://code.djangoproject.com/ticket/30554
        # Autoreload logs excessively, turn it down a bit.
        #
        "django.utils.autoreload": {
            "handlers": ["django"],
            "level": "INFO",
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

ELASTIC_APM["DEBUG"] = True

# Django debug toolbar
INSTALLED_APPS += ["debug_toolbar", "ddt_api_calls"]
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]
INTERNAL_IPS = ("127.0.0.1",)
DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False}
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
    "ddt_api_calls.panels.APICallsPanel",
]

# Django extensions
INSTALLED_APPS += ["django_extensions"]

# DRF - browsable API
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += [
    "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer"
]

# Django privates
SENDFILE_BACKEND = "django_sendfile.backends.development"

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
