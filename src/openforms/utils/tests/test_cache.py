import contextlib
import time
from unittest.mock import patch

from django.core.cache import caches
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import path


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "default",
        },
        "extra": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "extra",
        },
        "proxy1": {"BACKEND": "openforms.utils.cache.RequestProxyCache"},
        "proxy2": {
            "BACKEND": "openforms.utils.cache.RequestProxyCache",
            "LOCATION": "extra",
        },
    }
)
class NoRequestProxyCacheTests(TestCase):
    """
    Tests for cache usage outside of the request-response cycle.
    """

    def setUp(self) -> None:
        super().setUp()

        def clear_caches():
            for cache in caches.all():
                cache.clear()

        self.addCleanup(clear_caches)

    def test_cache_state(self):
        cache = caches["proxy1"]

        self.assertFalse(cache.active)

    def test_upstream_configuration(self):
        caches["default"].set("a-key", 1)
        caches["extra"].set("a-key", 2)

        with self.subTest("proxy 1"):
            value = caches["proxy1"].get("a-key")

            self.assertEqual(value, 1)

        with self.subTest("proxy 2"):
            value = caches["proxy2"].get("a-key")

            self.assertEqual(value, 2)

    def test_cache_read(self):
        cache = caches["proxy1"]

        with self.subTest("upstream cache miss"):
            value = cache.get("some-missing-key", default=None)

            self.assertIsNone(value)

        with self.subTest("upstream cache hit"):
            upstream = caches["default"]
            upstream.set("upstream-key", value="ok")

            value = cache.get("upstream-key")

            self.assertEqual(value, "ok")
            # check that the value is not stored
            self.assertTrue("upstream-key" in cache)
            local_key = cache.make_key("upstream-key")
            self.assertNotIn(local_key, cache._cache)

    def test_cache_add(self):
        with self.subTest("added to upstream"):
            added = caches["proxy1"].add("some-key", 123)

            self.assertTrue(added)

        with self.subTest("already present in upstream"):
            caches["extra"].add("some-key", 123)
            added = caches["proxy2"].add("some-key", 123)

            self.assertFalse(added)

    def test_cache_set(self):
        cache = caches["proxy1"]
        upstream = caches["default"]

        cache.set("set-a-key", 123)

        value = upstream.get("set-a-key")
        self.assertEqual(value, 123)
        local_key = cache.make_key("upstream-key")
        self.assertNotIn(local_key, cache._cache)

    def test_cache_touch(self):
        cache = caches["proxy1"]
        upstream = caches["default"]
        upstream.set("touch-key", 42, timeout=0.5)
        time.sleep(0.25)
        cache.touch("touch-key", timeout=1)
        time.sleep(0.75)

        value = upstream.get("touch-key")

        self.assertEqual(value, 42)

    def test_cache_delete(self):
        cache = caches["proxy1"]
        upstream = caches["default"]

        with self.subTest("delete in upstream"):
            upstream.set("delete-key", 42)

            cache.delete("delete-key")

            value = upstream.get("delete-key", None)
            self.assertIsNone(value)

        with self.subTest("does not exist"):
            result = cache.delete("bad-key")

            self.assertFalse(result)


urlpatterns = []


@contextlib.contextmanager
def test_view(view):
    with override_settings(ROOT_URLCONF=__name__):
        with patch(f"{__name__}.urlpatterns", new=[path("", view)]):
            yield


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "default",
        },
        "proxy": {"BACKEND": "openforms.utils.cache.RequestProxyCache"},
    },
    MIDDLEWARE=[],
)
class WithinRequestProxyCacheTests(TestCase):
    def setUp(self) -> None:
        super().setUp()

        def clear_caches():
            for cache in caches.all():
                cache.clear()

        self.addCleanup(clear_caches)

    def test_cache_active_in_request(self):
        client = Client()
        upstream = caches["default"]
        upstream.set("foo", "bar")

        def testview(request):
            cache = caches["proxy"]
            self.assertTrue(cache.active)
            value = cache.get("foo")

            self.assertEqual(value, "bar")
            key = cache.make_key("foo")
            self.assertIn(key, cache._cache)

            # delete from upstream cache, repeated access is fetched from local cache
            upstream.delete("foo")
            local_value = cache.get("foo")
            self.assertEqual(local_value, "bar")

            return HttpResponse("ok")

        with test_view(testview):
            try:
                client.get("/")
            except Exception:
                self.fail("Assertions in test view failed")

    def test_cache_active_in_request_cache_miss(self):
        client = Client()

        def testview(request):
            cache = caches["proxy"]
            value = cache.get("some-missing-key", None)

            self.assertIsNone(value)
            key = cache.make_key("some-missing-key")
            self.assertNotIn(key, cache._cache)

            return HttpResponse("ok")

        with test_view(testview):
            try:
                client.get("/")
            except Exception:
                self.fail("Assertions in test view failed")

    def test_cache_delete_deletes_local_copy(self):
        client = Client()
        upstream = caches["default"]
        cache = caches["proxy"]
        cache.set("key-to-delete", 123)

        def testview(request):
            value = cache.get("key-to-delete")
            self.assertEqual(value, 123)

            cache.delete("key-to-delete")

            self.assertIsNone(upstream.get("key-to-delete", default=None))
            self.assertIsNone(cache.get("key-to-delete", default=None))

            return HttpResponse("ok")

        with test_view(testview):
            try:
                client.get("/")
            except Exception:
                self.fail("Assertions in test view failed")
