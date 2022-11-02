from django.core.cache import caches


def clear_caches():
    for cache in caches.all():
        cache.clear()
