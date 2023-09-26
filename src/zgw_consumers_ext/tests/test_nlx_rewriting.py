from django.test import TestCase

import requests_mock
from zgw_consumers.constants import AuthTypes

from .factories import ServiceFactory

DUMMY_SCHEMA = {
    "openapi": "3.0.1",
    "paths": {},
}


class NLXClientTests(TestCase):
    @requests_mock.Mocker()
    def test_request_url_and_response_data_rewritten(self, m):
        nlx_service = ServiceFactory.create(
            label="Service with NLX",
            api_root="https://example.com/",
            auth_type=AuthTypes.no_auth,
            nlx="http://localhost:8081/:serial-number/:service/",
        )
        client = nlx_service.build_client()
        client.schema = DUMMY_SCHEMA
        m.get(
            "http://localhost:8081/:serial-number/:service/some-resource",
            json=lambda req, _: {"url": req.url},
        )

        response_data = client.request(
            path="some-resource",
            operation="dummy-operation",
            method="GET",
        )

        self.assertEqual(m.last_request.method, "GET")
        self.assertEqual(
            m.last_request.url,
            "http://localhost:8081/:serial-number/:service/some-resource",
        )
        self.assertEqual(response_data, {"url": "https://example.com/some-resource"})
