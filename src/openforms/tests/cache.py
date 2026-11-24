import json
import pickle
from typing import TYPE_CHECKING

from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache
from django.core.cache.backends.dummy import DummyCache
from django.core.cache.backends.locmem import LocMemCache
from django.core.serializers.json import DjangoJSONEncoder

import msgspec

JSON_DECODER = msgspec.json.Decoder()


if TYPE_CHECKING:
    MixinBase = BaseCache
else:
    MixinBase = object


class JSONMixin(MixinBase):
    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        # don't use msgspec, because it understands dataclasses
        value = json.dumps(value, cls=DjangoJSONEncoder)
        return super().add(key, value, timeout=timeout, version=version)

    def get(self, key, default=None, version=None):
        result = super().get(key, default=default, version=version)
        if result == default:
            return default
        return JSON_DECODER.decode(result)

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        # don't use msgspec, because it understands dataclasses
        value = json.dumps(value, cls=DjangoJSONEncoder)
        return super().set(key, value, timeout=timeout, version=version)


class JSONLocMemCache(JSONMixin, LocMemCache):
    """
    A local memory cache backend that forces JSON serialization.

    Set up in the CI settings, this backend catches code that tries to put non-JSON
    compatible data in the cache by forcibly encoding values.
    """

    def incr(self, key, delta=1, version=None):
        key = self.make_and_validate_key(key, version=version)
        with self._lock:
            if self._has_expired(key):
                self._delete(key)
                raise ValueError(f"Key '{key}' not found")
            pickled = self._cache[key]
            value = JSON_DECODER.decode(pickle.loads(pickled))
            new_value = value + delta
            pickled = pickle.dumps(
                json.dumps(new_value, cls=DjangoJSONEncoder), self.pickle_protocol
            )
            self._cache[key] = pickled
            self._cache.move_to_end(key, last=False)
        return new_value


class JSONDummyCache(JSONMixin, DummyCache):
    """
    A local dummy cache backend that forces JSON serialization.

    Set up in the CI settings, this backend catches code that tries to put non-JSON
    compatible data in the cache by forcibly encoding values.
    """
