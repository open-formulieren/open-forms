import socket

from django.conf import settings
from django.test import override_settings

NOOP_CACHES = {
    name: {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    for name in settings.CACHES.keys()
}


disable_2fa = override_settings(TWO_FACTOR_PATCH_ADMIN=False)


def can_connect(hostname: str):
    # adapted from https://stackoverflow.com/a/28752285
    hostname, port = hostname.split(":")
    try:
        host = socket.gethostbyname(hostname)
        s = socket.create_connection((host, port), 2)
        s.close()
        return True
    except Exception:
        return False
