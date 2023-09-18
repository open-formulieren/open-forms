from unittest import TestCase

import requests_mock
from requests import Session

from ..client import APIClient


class DirectInstantiationTests(TestCase):
    def test_defaults_from_requests_session(self):
        vanilla_session = Session()

        client = APIClient("https://example.com")

        for attr in Session.__attrs__:
            if attr == "adapters":
                continue
            with self.subTest(attr=attr):
                vanilla_value = getattr(vanilla_session, attr)
                client_value = getattr(client, attr)

                self.assertEqual(client_value, vanilla_value)
