# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2019 - 2020 Dimpact
"""
Continuous integration settings module.
"""
import os
import warnings

os.environ.setdefault("IS_HTTPS", "no")
os.environ.setdefault("SECRET_KEY", "dummy")

from .base import *  # noqa isort:skip

CACHES.update(
    {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        # See: https://github.com/jazzband/django-axes/blob/master/docs/configuration.rst#cache-problems
        "axes": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "oidc": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
)

# shut up logging
LOGGING["loggers"].update(
    {
        "openforms.api.exception_handling": {
            "handlers": ["console"],
            "level": "CRITICAL",
            "propagate": False,
        },
    }
)


ENVIRONMENT = "CI"

#
# Django-axes
#
AXES_BEHIND_REVERSE_PROXY = False

# Django privates
SENDFILE_BACKEND = "django_sendfile.backends.development"

# Two factor auth
TWO_FACTOR_FORCE_OTP_ADMIN = False

# THOU SHALT NOT USE NAIVE DATETIMES
warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)
