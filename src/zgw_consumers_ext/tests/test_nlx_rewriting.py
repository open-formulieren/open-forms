from django.test import TestCase

import requests_mock
from zgw_consumers.constants import AuthTypes

from ..api_client import build_client
from .factories import ServiceFactory


class NLXClientTests(TestCase):
    @requests_mock.Mocker()
    def test_request_url_and_response_data_rewritten(self, m):
        nlx_service = ServiceFactory.create(
            label="Service with NLX",
            api_root="https://example.com/",
            auth_type=AuthTypes.no_auth,
            nlx="http://localhost:8081/:serial-number/:service/",
        )
        client = build_client(nlx_service)

        m.get(
            "http://localhost:8081/:serial-number/:service/some-resource",
            json=lambda req, _: {"url": req.url},
        )

        with client:
            response_data = client.get("some-resource").json()

        self.assertEqual(m.last_request.method, "GET")
        self.assertEqual(
            m.last_request.url,
            "http://localhost:8081/:serial-number/:service/some-resource",
        )
        self.assertEqual(response_data, {"url": "https://example.com/some-resource"})
