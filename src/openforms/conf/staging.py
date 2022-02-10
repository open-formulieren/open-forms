"""
Staging environment settings module.
This *should* be nearly identical to production.
"""
import os

os.environ.setdefault("ENVIRONMENT", "staging")
# NOTE: watch out for multiple projects using the same cache!
os.environ.setdefault("CACHE_DEFAULT", "127.0.0.1:6379/1")
os.environ.setdefault("CACHE_AXES", "127.0.0.1:6379/3")
os.environ.setdefault("CACHE_OIDC", "127.0.0.1:6379/5")
os.environ.setdefault("CACHE_PORTALOCKER", "127.0.0.1:6379/7")

from .production import *  # noqa isort:skip
