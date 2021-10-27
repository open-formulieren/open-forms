from unittest import skipIf

from django.test import SimpleTestCase, override_settings

import requests

from .utils import can_connect

HOST = "github.com:443"


@skipIf(
    not can_connect(HOST), "Can't connect to host - possibly running tests offline."
)
class RequestsTimeoutTests(SimpleTestCase):
    @override_settings(DEFAULT_TIMEOUT_REQUESTS=0.00001)
    def test_timeout_happens(self):
        with self.assertRaises(requests.Timeout):
            requests.head(f"https://{HOST}")

    @override_settings(DEFAULT_TIMEOUT_REQUESTS=20.0)
    def test_timeout_doesnt_happen(self):
        try:
            requests.head(f"https://{HOST}")
        except requests.Timeout:
            self.fail("Unexpected timeout")

    def test_is_only_default_value(self):
        @override_settings(DEFAULT_TIMEOUT_REQUESTS=0.00001)
        def test_timeout_happens(self):
            try:
                requests.head(f"https://{HOST}", timeout=20.0)
            except requests.Timeout:
                self.fail("Unexpected timeout")
