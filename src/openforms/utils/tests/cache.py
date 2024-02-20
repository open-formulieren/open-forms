from django.core.cache import caches


def clear_caches():
    for alias in caches:
        # clearing the distributed session locks causes issues when tests are run
        # in parallel (--parallel X)
        if alias == "portalocker":
            continue
        cache = caches[alias]
        cache.clear()
