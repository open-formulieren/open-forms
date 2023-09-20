"""
Test the client factory from SOAPService configuration.
"""
from pathlib import Path

from django.test import TestCase

from simple_certmanager_ext.tests.factories import CertificateFactory

from ..client import build_client
from ..constants import EndpointSecurity
from .factories import SoapServiceFactory

WSDL = Path(__file__).parent.resolve() / "data" / "sample.wsdl"
WSDL_URI = str(WSDL)


class ClientTransportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.client_cert_only = CertificateFactory.create(
            label="Gateway client certificate",
            public_certificate__filename="client_cert.pem",
        )
        cls.client_cert_and_privkey = CertificateFactory.create(
            label="Gateway client certificate",
            with_private_key=True,
            public_certificate__filename="client_cert.pem",
            private_key__filename="client_key.pem",
        )
        cls.server_cert = CertificateFactory.create(
            label="Gateway server certificate",
            public_certificate__filename="server.pem",
        )

    def test_no_server_cert_specified(self):
        service = SoapServiceFactory.build(url=WSDL_URI)

        client = build_client(service)

        self.assertIs(
            client.transport.session.verify, True
        )  # not just truthy, but identity check

    def test_server_cert_specified(self):
        service = SoapServiceFactory.build(
            url=WSDL_URI, server_certificate=self.server_cert
        )

        client = build_client(service)

        self.assertEqual(
            client.transport.session.verify, self.server_cert.public_certificate.path
        )

    def test_no_client_cert_specified(self):
        service = SoapServiceFactory.build(url=WSDL_URI)

        client = build_client(service)

        self.assertIsNone(client.transport.session.cert)

    def test_client_cert_only_public_cert_specified(self):
        service = SoapServiceFactory.build(
            url=WSDL_URI, client_certificate=self.client_cert_only
        )

        client = build_client(service)

        self.assertEqual(
            client.transport.session.cert, self.client_cert_only.public_certificate.path
        )

    def test_client_cert_public_cert_and_privkey_specified(self):
        service = SoapServiceFactory.build(
            url=WSDL_URI, client_certificate=self.client_cert_and_privkey
        )

        client = build_client(service)

        self.assertEqual(
            client.transport.session.cert,
            (
                self.client_cert_and_privkey.public_certificate.path,
                self.client_cert_and_privkey.private_key.path,
            ),
        )

    def test_incomplete_client_cert_configured(self):
        service = SoapServiceFactory.build(
            url=WSDL_URI,
            client_certificate=CertificateFactory.create(
                public_certificate=None,
                private_key=None,
            ),
        )

        client = build_client(service)

        self.assertIsNone(client.transport.session.cert)

    def test_no_auth(self):
        service = SoapServiceFactory.build(url=WSDL_URI)
        assert service.endpoint_security == ""

        client = build_client(service)

        self.assertIsNone(client.transport.session.auth)

    def test_basic_auth(self):
        username_password = (
            EndpointSecurity.basicauth,
            EndpointSecurity.wss_basicauth,
        )
        for security in username_password:
            with self.subTest(security=security):
                service = SoapServiceFactory.build(
                    url=WSDL_URI,
                    endpoint_security=security,
                    user="admin",
                    password="supersecret",
                )

                client = build_client(service)

                self.assertIsNotNone(client.transport.session.auth)
