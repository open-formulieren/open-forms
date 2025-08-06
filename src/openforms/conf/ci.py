# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2019 - 2020 Dimpact
"""
Continuous integration settings module.
"""
# ruff: noqa: F401 F405 TID253

import os
import warnings

# Importing the idna module has an IO side-effect to load the data, which is a rather
# big file. Pre-loading this in the settings file populates the python module cache,
# preventing flakiness in hypothesis tests that hit this code path.
import idna

# Heavy imports, can interfere with some tests making use of hypothesis' deadline:
import weasyprint

os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("SECRET_KEY", "dummy")
os.environ.setdefault("SENDFILE_BACKEND", "django_sendfile.backends.development")

# Do not log requests in CI/tests:
#
# * overhead making tests slower
# * it conflicts with SimpleTestCase in some cases when the run-time configuration is
#   looked up from the django-solo model
os.environ.setdefault("LOG_OUTGOING_REQUESTS", "no")

os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from .base import *  # noqa isort:skip
from .utils import mute_logging  # noqa isort:skip

CACHES.update(
    {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        # See: https://github.com/jazzband/django-axes/blob/master/docs/configuration.rst#cache-problems
        "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "oidc": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
)

# shut up logging
mute_logging(LOGGING)

# don't spend time on password hashing in tests/user factories
PASSWORD_HASHERS = ["django.contrib.auth.hashers.UnsaltedMD5PasswordHasher"]

ENVIRONMENT = "CI"

#
# Django-axes
#
AXES_BEHIND_REVERSE_PROXY = False

# THOU SHALT NOT USE NAIVE DATETIMES
warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)

#
# Celery
#
CELERY_BROKER_TRANSPORT_OPTIONS = {
    # when running in CI with a deliberately broken broker URL, tests should fail/error
    # instead of retrying forever if the broker isn't available (which it won't be).
    "max_retries": 0,
}
