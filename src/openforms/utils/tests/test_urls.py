from django.test import RequestFactory, TestCase, override_settings

from openforms.utils.urls import build_absolute_uri


@override_settings(IS_HTTPS=True, BASE_URL="http://test/")  # IS_HTTPS is ignored
class BuildAbsoluteUriTests(TestCase):
    def test_basic(self):
        url = build_absolute_uri("/aa/bb/?x=1")
        self.assertEqual("http://test/aa/bb/?x=1", url)

        url = build_absolute_uri("/aa/bb?x=1")
        self.assertEqual("http://test/aa/bb?x=1", url)

        url = build_absolute_uri("aa/bb/?x=1")
        self.assertEqual("http://test/aa/bb/?x=1", url)

        url = build_absolute_uri("aa/bb?x=1")
        self.assertEqual("http://test/aa/bb?x=1", url)

    def test_basic_with_request(self):
        request = RequestFactory().get("/dummy")

        url = build_absolute_uri("/aa/bb/?x=1", request=request)
        self.assertEqual("http://testserver/aa/bb/?x=1", url)

        url = build_absolute_uri("/aa/bb?x=1", request=request)
        self.assertEqual("http://testserver/aa/bb?x=1", url)

        url = build_absolute_uri("aa/bb/?x=1", request=request)
        self.assertEqual("http://testserver/aa/bb/?x=1", url)

        url = build_absolute_uri("aa/bb?x=1", request=request)
        self.assertEqual("http://testserver/aa/bb?x=1", url)

    def test_base_url_with_path(self):
        with self.settings(BASE_URL="http://test/pre/path/"):
            url = build_absolute_uri("/aa/bb")
            self.assertEqual("http://test/aa/bb", url)

            url = build_absolute_uri("aa/bb")
            self.assertEqual("http://test/aa/bb", url)
