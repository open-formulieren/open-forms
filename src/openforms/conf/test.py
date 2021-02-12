"""
Staging environment settings module.
This *should* be nearly identical to production.
"""
import os

os.environ.setdefault("ENVIRONMENT", "test")
# NOTE: watch out for multiple projects using the same cache!
os.environ.setdefault("CACHE_DEFAULT", "127.0.0.1:6379/0")

from .production import *  # noqa isort:skip

for db_alias in DATABASES.keys():
    del DATABASES[db_alias]["CONN_MAX_AGE"]
