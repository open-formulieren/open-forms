# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2021 Dimpact
from django.test import RequestFactory, SimpleTestCase, override_settings, tag


@tag("x-forwarded-for")
class XForwardedHostTests(SimpleTestCase):
    """
    Test the opt-in behaviour of the X-Forwarded-For header.
    """

    factory = RequestFactory()

    def test_default_disabled(self):
        request = self.factory.get(
            "/",
            HTTP_X_FORWARDED_HOST="evil.com",
        )

        self.assertEqual(
            request.get_host(),
            "testserver",
        )

    @override_settings(
        USE_X_FORWARDED_HOST=True,
        ALLOWED_HOSTS=["upstream.proxy"],
    )
    def test_enabled(self):
        request = self.factory.get(
            "/",
            HTTP_X_FORWARDED_HOST="upstream.proxy",
        )

        self.assertEqual(
            request.get_host(),
            "upstream.proxy",
        )
