"""
Production environment settings module.
Tweaks the base settings so that caching mechanisms are used where possible,
and HTTPS is leveraged where possible to further secure things.
"""
import os

os.environ.setdefault("ENVIRONMENT", "production")
# NOTE: watch out for multiple projects using the same cache!
os.environ.setdefault("CACHE_DEFAULT", "127.0.0.1:6379/2")
os.environ.setdefault("CACHE_AXES", "127.0.0.1:6379/4")
os.environ.setdefault("CACHE_OIDC", "127.0.0.1:6379/6")
os.environ.setdefault("CACHE_PORTALOCKER", "127.0.0.1:6379/8")

from .base import *  # noqa isort:skip

# Database performance
for db_config in DATABASES.values():
    db_config["CONN_MAX_AGE"] = 60  # Lifetime of a database connection for performance.

# Caching sessions.
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Caching templates.
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    ("django.template.loaders.cached.Loader", TEMPLATE_LOADERS)
]

# The file storage engine to use when collecting static files with the
# collectstatic management command.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Production logging facility.

# Production logging facility.
handlers = ["console"] if LOG_STDOUT else ["django"]

LOGGING["loggers"].update(
    {
        "django": {"handlers": handlers, "level": "INFO", "propagate": True},
        "django.security.DisallowedHost": {
            "handlers": handlers,
            "level": "CRITICAL",
            "propagate": False,
        },
    }
)

# Only set this when we're behind a reverse proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True  # Sets X-Content-Type-Options: nosniff
SECURE_BROWSER_XSS_FILTER = True  # Sets X-XSS-Protection: 1; mode=block

#
# Custom settings overrides
#
SHOW_ALERT = False

##############################
#                            #
# 3RD PARTY LIBRARY SETTINGS #
#                            #
##############################
