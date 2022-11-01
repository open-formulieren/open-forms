from pathlib import Path

from django.core.cache import caches

TEST_FILES = Path(__file__).parent.resolve() / "data"


def clear_caches():
    for cache in caches.all():
        cache.clear()
