"""
Test the base client primitives.

Tests the aspects:

* session/connection pool management
* auth parameters from service
* request body generation via templates
"""
from base64 import b64decode
from unittest.mock import patch

from django.test import SimpleTestCase

import requests_mock
from privates.test import temp_private_root

from soap.constants import EndpointSecurity
from stuf.xml import fromstring

from ..client import BaseClient
from .factories import StufServiceFactory


@temp_private_root()
class BaseClientRequestsInterfaceTests(SimpleTestCase):
    @patch("stuf.client.Session.close")
    @requests_mock.Mocker()
    def test_usage_as_context_manager(self, mock_close, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service"
        )
        m.post("https://example.com/service")
        client = BaseClient(service)

        with client:
            with self.subTest("First call"):
                client.request("soapAction", body="")

                mock_close.assert_not_called()

            with self.subTest("Second call"):
                client.request("soapAction", body="")

                mock_close.assert_not_called()

        mock_close.assert_called_once()

    @patch("stuf.client.Session.close")
    def test_usage_as_context_manager_without_using_session(self, mock_close):
        service = StufServiceFactory.build()
        client = BaseClient(service)

        with client:
            pass

        mock_close.assert_not_called()

    @patch("stuf.client.Session.close")
    @requests_mock.Mocker()
    def test_usage_without_context_manager(self, mock_close, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service"
        )
        m.post("https://example.com/service")
        client = BaseClient(service)

        with self.subTest("First bare call"):
            client.request("soapAction", body="")

            mock_close.assert_called_once()

        with self.subTest("Second bare call"):
            client.request("soapAction", body="")

            self.assertEqual(mock_close.call_count, 2)

    @requests_mock.Mocker()
    def test_auth_params_passed_username_password(self, m):
        m.post("https://example.com/service")
        yes_basic_auth = (EndpointSecurity.basicauth, EndpointSecurity.wss_basicauth)
        no_basic_auth = (EndpointSecurity.wss,)

        for endpoint_security in yes_basic_auth:
            m.reset()
            with self.subTest(endpoint_security=endpoint_security):
                service = StufServiceFactory.build(
                    soap_service__url="https://example.com/service",
                    soap_service__endpoint_security=endpoint_security,
                    soap_service__user="nico",
                    soap_service__password="Uuuulkenberg",
                )
                client = BaseClient(service)

                client.request("soapAction", body="")

                headers = m.last_request.headers
                self.assertIn("Authorization", headers)
                scheme, parameters = headers["Authorization"].split(" ")
                self.assertEqual(scheme, "Basic")
                self.assertEqual(b64decode(parameters), b"nico:Uuuulkenberg")

        for endpoint_security in no_basic_auth:
            m.reset()
            with self.subTest(endpoint_security=endpoint_security):
                service = StufServiceFactory.build(
                    soap_service__url="https://example.com/service",
                    soap_service__endpoint_security=endpoint_security,
                    soap_service__user="nico",
                    soap_service__password="Uuuulkenberg",
                )
                client = BaseClient(service)

                client.request("soapAction", body="")

                headers = m.last_request.headers
                self.assertNotIn("Authorization", headers)

    @requests_mock.Mocker()
    def test_mtls_server_cert_specified(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service",
            soap_service__with_server_cert=True,
        )
        m.post("https://example.com/service")
        client = BaseClient(service)

        client.request("soapAction", body="")

        self.assertEqual(
            m.last_request.verify,
            service.soap_service.server_certificate.public_certificate.path,
        )

    @requests_mock.Mocker()
    def test_mtls_no_server_cert_specified(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service",
            soap_service__with_server_cert=False,
        )
        assert not service.soap_service.server_certificate
        m.post("https://example.com/service")
        client = BaseClient(service)

        client.request("soapAction", body="")

        self.assertIs(m.last_request.verify, True)

    @requests_mock.Mocker()
    def test_mtls_client_cert_specified_public_certificate_missing(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service",
            soap_service__with_client_cert=True,
            soap_service__client_certificate__public_certificate="",
        )
        assert service.soap_service.client_certificate
        assert not service.soap_service.client_certificate.public_certificate
        m.post("https://example.com/service")
        client = BaseClient(service)

        client.request("soapAction", body="")

        self.assertIsNone(m.last_request.cert)

    @requests_mock.Mocker()
    def test_mtls_no_client_certificate(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service",
            soap_service__with_server_cert=False,
            soap_service__with_client_cert=False,
        )
        assert not service.soap_service.client_certificate

        m.post("https://example.com/service")
        client = BaseClient(service)

        client.request("soapAction", body="")

        # implementation details in requests.adapters.HTTPAdapter.cert_verify
        self.assertIsNone(m.last_request.cert)

    @requests_mock.Mocker()
    def test_mtls_client_certificate_only(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service",
            soap_service__with_server_cert=False,
            soap_service__with_client_cert=True,
            soap_service__client_certificate__with_private_key=False,
        )
        assert service.soap_service.client_certificate
        assert not service.soap_service.client_certificate.private_key

        m.post("https://example.com/service")
        client = BaseClient(service)

        client.request("soapAction", body="")

        # implementation details in requests.adapters.HTTPAdapter.cert_verify
        self.assertEqual(
            m.last_request.cert,
            service.soap_service.client_certificate.public_certificate.path,
        )

    @requests_mock.Mocker()
    def test_mtls_client_certificate_and_privkey(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service",
            soap_service__with_server_cert=False,
            soap_service__with_client_cert=True,
            soap_service__client_certificate__with_private_key=True,
        )
        assert service.soap_service.client_certificate
        assert service.soap_service.client_certificate.private_key

        m.post("https://example.com/service")
        client = BaseClient(service)

        client.request("soapAction", body="")

        # implementation details in requests.adapters.HTTPAdapter.cert_verify
        self.assertEqual(
            m.last_request.cert,
            (
                service.soap_service.client_certificate.public_certificate.path,
                service.soap_service.client_certificate.private_key.path,
            ),
        )

    @requests_mock.Mocker()
    def test_soap_action_in_headers(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service"
        )
        m.post("https://example.com/service")
        client = BaseClient(service)
        client.sector_alias = "sa"

        client.request("someSOAPAction", body="")

        headers = m.last_request.headers
        self.assertIn("SOAPAction", headers)
        self.assertEqual(
            headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/sa/0310/someSOAPAction",
        )


@requests_mock.Mocker()
class BaseClientBodyTests(SimpleTestCase):
    def test_templated_request(self, m):
        service = StufServiceFactory.build(
            soap_service__url="https://example.com/service"
        )
        m.post("https://example.com/service")
        client = BaseClient(service)
        client.soap_security_expires_minutes = 10

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
                client = BaseClient(service)
                client.soap_security_expires_minutes = 10

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
