from django.conf import settings
from django.test import override_settings

NOOP_CACHES = {
    name: {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    for name in settings.CACHES.keys()
}


disable_2fa = override_settings(TWO_FACTOR_PATCH_ADMIN=False)
