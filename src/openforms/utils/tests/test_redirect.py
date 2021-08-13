from django.test import TestCase, override_settings

from ..redirect import allow_redirect_url


class RedirectTests(TestCase):
    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False,
        CORS_ALLOWED_ORIGINS=[],
        CORS_ALLOWED_ORIGIN_REGEXES=[],
    )
    def test_allow_redirect_url(self):
        self.assertEqual(allow_redirect_url("http://foo.bar"), False)
        self.assertEqual(allow_redirect_url("http://foo.bar/bazz"), False)
        self.assertEqual(allow_redirect_url("https://foo.bar"), False)
        self.assertEqual(allow_redirect_url("http://bazz.buzz"), False)

        with self.settings(
            CORS_ALLOW_ALL_ORIGINS=True,
        ):
            self.assertEqual(allow_redirect_url("http://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://foo.bar/bazz"), True)
            self.assertEqual(allow_redirect_url("https://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://bazz.buzz"), True)

        with self.settings(
            CORS_ALLOWED_ORIGINS=["http://foo.bar"],
        ):
            self.assertEqual(allow_redirect_url("http://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://foo.bar/bazz"), True)
            self.assertEqual(allow_redirect_url("https://foo.bar"), False)
            self.assertEqual(allow_redirect_url("http://bazz.buzz"), False)

        with self.settings(
            CORS_ALLOWED_ORIGIN_REGEXES=[r".*foo.*"],
        ):
            self.assertEqual(allow_redirect_url("http://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://foo.bar/bazz"), True)
            self.assertEqual(allow_redirect_url("https://foo.bar"), True)
            self.assertEqual(allow_redirect_url("http://bazz.buzz"), False)
