#
# Any machine specific settings when using development settings.
#
import os
import sys

from .dev import LOGGING as _LOGGING
from .utils import config

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
    #     LOGGING = None


if "CELERY_TASK_ALWAYS_EAGER" in os.environ:
    CELERY_TASK_ALWAYS_EAGER = True

if log_level := os.environ.get("LOG_LEVEL"):
    for logger in _LOGGING["loggers"].values():
        logger["level"] = log_level

# make the language code configurable via envvars
LANGUAGE_CODE = config("LANGUAGE_CODE", "nl")

# allow SPA dev server and API on different ports
# CORS_ALLOW_ALL_ORIGINS = True

# run celery tasks so submissions get processed in dev server
# Ceveat emptor: this breaks test isolation and breaks a few tests in the suite
# CELERY_TASK_ALWAYS_EAGER = True

# don't force tokens in dev server
TWO_FACTOR_PATCH_ADMIN = False
TWO_FACTOR_FORCE_OTP_ADMIN = False
