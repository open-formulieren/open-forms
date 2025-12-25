#
# Any machine specific settings when using development settings.
#
import os
import sys

from maykin_common.config import config

from .dev import LOGGING

# Configure your database via the DB_* envvars in .env, see also dotenv.example file.

SILKY_PYTHON_PROFILER = True

if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.UnsaltedMD5PasswordHasher"]

    # if you have a separate postgres cluster purely for testing, change the port number
    # and use the superuser
    # DATABASES["default"]["PORT"] = 5433
    # DATABASES["default"]["USER"] = "postgres"

    # Silence logging during testing
    # if "VERBOSE" not in os.environ:
    #     mute_logging(LOGGING)


# run celery tasks so submissions get processed in dev server
# Ceveat emptor: this breaks test isolation and breaks a few tests in the suite
if config("CELERY_TASK_ALWAYS_EAGER", default=False):
    CELERY_TASK_ALWAYS_EAGER = True

#
# LOGGING
#

# Log DB queries to file and console
# LOGGING["loggers"]["django.db.backends"] = {
#     "handlers": ["django", "console"],
#     "level": "DEBUG",
#     "propagate": False,
# }

if log_level := os.environ.get("LOG_LEVEL"):
    for logger in LOGGING["loggers"].values():
        logger["level"] = log_level


# make the language code configurable via envvars
LANGUAGE_CODE = config("LANGUAGE_CODE", default="nl")

# allow SPA dev server and API on different ports
# CORS_ALLOW_ALL_ORIGINS = True
