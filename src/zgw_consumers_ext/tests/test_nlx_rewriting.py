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

    @requests_mock.Mocker()
    def test_non_json_response_data(self, m):
        nlx_service = ServiceFactory.create(
            label="Service with NLX",
            api_root="https://example.com/",
            auth_type=AuthTypes.no_auth,
            nlx="http://localhost:8081/:serial-number/:service/",
        )
        client = build_client(nlx_service)

        m.get(
            "http://localhost:8081/:serial-number/:service/some-resource",
            content=b"AAAAA",
        )

        with client:
            response_data = client.get("some-resource").content

        self.assertEqual(m.last_request.method, "GET")
        self.assertEqual(
            m.last_request.url,
            "http://localhost:8081/:serial-number/:service/some-resource",
        )
        self.assertEqual(response_data, b"AAAAA")

    @requests_mock.Mocker()
    def test_service_without_nlx(self, m):
        ServiceFactory.create(
            label="Service with NLX",
            api_root="https://example.com/",
            auth_type=AuthTypes.no_auth,
            nlx="http://localhost:8081/:serial-number/:service/",
        )
        normal_service = ServiceFactory.create(
            label="Service without NLX",
            api_root="https://second.example.com/",
            auth_type=AuthTypes.no_auth,
        )
        client = build_client(normal_service)
        m.get(
            "https://second.example.com/some-resource",
            json={"url": "https://example.com"},
        )

        with client:
            response_data = client.get("some-resource").json()

        self.assertEqual(m.last_request.method, "GET")
        self.assertEqual(
            m.last_request.url,
            "https://second.example.com/some-resource",
        )
        # no rewriting of any sorts
        self.assertEqual(response_data, {"url": "https://example.com"})
