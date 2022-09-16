import threading

from django.core import signals
from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache


class RequestProxyCache(BaseCache):
    """
    Store and proxy cache items on a per-request basis.

    This cache only operates during a request-response cycle.

    When a cache key is not found, it is looked up in the configured upstream cache.
    All operations like setting/deleting/clearing this cache are proxied to the
    upstream cache.

    Values cached in memory do not honor the timeouts, as the cache only exists for the
    scope of a single request.
    """

    _storage = threading.local()

    def __init__(self, upstream: str, params):
        super().__init__(params)
        upstream = upstream or DEFAULT_CACHE_ALIAS
        self.upstream_cache = caches[upstream]
        self._reset()

    def _reset(self):
        self._storage.__dict__.clear()
        self._storage.in_request_response_cycle = False

    @property
    def active(self):
        return self._storage.in_request_response_cycle

    @property
    def _cache(self):
        return self._storage.__dict__

    def mark_request_started(self):
        self._storage.in_request_response_cycle = True

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        added = self.upstream_cache.add(key, value, timeout=timeout, version=version)
        if added:
            _key = self.make_key(key, version=version)
            self._set(_key, value)
        return added

    def get(self, key, default=None, version=None):
        _key = self.make_key(key, version=version)
        local_value = self._cache.get(_key, self._missing_key)
        if self.active and local_value is not self._missing_key:
            return local_value

        value = self.upstream_cache.get(key, default=default, version=version)
        if self.active and value != default:
            _key = self.make_key(key, version=version)
            self._set(_key, value)
        return value

    def _set(self, key, value):
        if not self.active:
            return
        self._cache[key] = value

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        self.upstream_cache.set(key, value, timeout=timeout, version=version)
        _key = self.make_key(key, version=version)
        self._set(_key, value)

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        return self.upstream_cache.touch(key, timeout=timeout, version=version)

    def delete(self, key, version=None):
        deleted = self.upstream_cache.delete(key, version=version)
        if deleted:
            _key = self.make_key(key, version=version)
            if _key in self._cache:
                del self._cache[_key]
        return deleted

    def clear(self):
        self._reset()
        return self.upstream_cache.clear()

    def close(self):
        self.upstream_cache.close()
        self._reset()


def mark_request_proxy_caches(**kwargs):
    for cache in caches.all():
        if not isinstance(cache, RequestProxyCache):
            continue
        cache.mark_request_started()


signals.request_started.connect(
    mark_request_proxy_caches,
    dispatch_uid="openforms.cache.mark_request_start",
)
