"""
Test the base client primitives.

Note that general HTTP semantics are covered in the :module:`api_client` tests package.

Aspects tested:

* relevant SOAP HTTP headers
* request body generation via templates
"""

from django.test import SimpleTestCase

import requests_mock
from ape_pie import InvalidURLError
from privates.test import temp_private_root

from soap.constants import EndpointSecurity

from ..client import BaseClient
from ..models import StufService
from ..service_client_factory import ServiceClientFactory, get_client_init_kwargs
from ..xml import fromstring
from .factories import StufServiceFactory


def build_client(service: StufService, **attrs):
    factory = ServiceClientFactory(service)
    client = BaseClient.configure_from(factory, **get_client_init_kwargs(service))
    for key, value in attrs.items():
        setattr(client, key, value)
    return client


@temp_private_root()
class BaseClientRequestsInterfaceTests(SimpleTestCase):
    @requests_mock.Mocker()
    def test_soap_action_in_headers(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service"
        )
        m.post("https://example.com/service")
        client = build_client(service, sector_alias="sa")

        client.soap_request("someSOAPAction", body="")

        headers = m.last_request.headers
        self.assertIn("SOAPAction", headers)
        self.assertEqual(
            headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/sa/0310/someSOAPAction",
        )

    def test_url_and_path_sanitization(self):
        service = StufServiceFactory.build(soap_service__url="https://example.com/")
        client = build_client(service, sector_alias="sa")

        with self.subTest("Absolute URL"):
            with self.assertRaises(InvalidURLError):
                client.request("ANY", url="https://other-base.example.com")

        with self.subTest("non-existing endpoint type"):
            with self.assertRaises(InvalidURLError):
                client.request("ANY", url="i-do-not-exist")


@requests_mock.Mocker()
class BaseClientBodyTests(SimpleTestCase):
    def test_templated_request(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service"
        )
        m.post("https://example.com/service")
        client = build_client(service, soap_security_expires_minutes=10)

        client.templated_request(
            "someSOAPAction",
            template="stuf/soap_envelope.xml",
            context={"foo": "bar"},
        )

        body = m.last_request.body
        xml_doc = fromstring(body)

        envelope = xml_doc.xpath("//*[local-name()='Envelope']")
        self.assertEqual(len(envelope), 1)

        header = xml_doc.xpath("//*[local-name()='Header']")
        self.assertEqual(len(header), 1)

        body = xml_doc.xpath("//*[local-name()='Body']")
        self.assertEqual(len(body), 1)

    def test_templated_request_has_security(self, m):
        m.post("https://example.com/service")
        yes_security = (
            ({"soap_service__endpoint_security": EndpointSecurity.wss}, False),
            (
                {
                    "soap_service__endpoint_security": EndpointSecurity.wss_basicauth,
                    "soap_service__user": "nico",
                    "soap_service__password": "Uuuulkenberg",
                },
                True,
            ),
        )

        for endpoint_security, basicauth_expected in yes_security:
            m.reset()
            with self.subTest(endpoint_security, basicauth_expected=basicauth_expected):
                service = StufServiceFactory.build(
                    soap_service__url="https://example.com/service",
                    **endpoint_security,
                )
                client = build_client(service, soap_security_expires_minutes=10)

                client.templated_request(
                    "someSOAPAction",
                    template="stuf/soap_envelope.xml",
                    context={"foo": "bar"},
                )

                body = m.last_request.body
                xml_doc = fromstring(body)

                security = xml_doc.xpath("//*[local-name()='Security']")
                self.assertEqual(len(security), 1)

                timestamp = security[0].xpath("./*[local-name()='Timestamp']")
                self.assertEqual(len(timestamp), 1)

                username_token = security[0].xpath("./*[local-name()='UsernameToken']")
                num_expected = 1 if basicauth_expected else 0
                self.assertEqual(len(username_token), num_expected)
