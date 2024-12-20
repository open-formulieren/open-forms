"""
Test the client factory from SOAPService configuration.
"""

from pathlib import Path

from django.test import TestCase

import requests_mock
from ape_pie import InvalidURLError
from requests.exceptions import RequestException
from simple_certmanager.test.factories import CertificateFactory
from zeep.exceptions import XMLSyntaxError
from zeep.wsse import Signature, UsernameToken

from openforms.utils.tests.vcr import OFVCRMixin

from ..client import SOAPSession, build_client
from ..constants import EndpointSecurity
from ..session_factory import SessionFactory
from .factories import SoapServiceFactory

DATA_DIR = Path(__file__).parent / "data"
WSDL = DATA_DIR / "sample.wsdl"
WSDL_URI = str(WSDL)


class ClientTransportTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = DATA_DIR

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
        cls.server_cert_and_privkey = CertificateFactory.create(
            label="Gateway server certificate",
            public_certificate__filename="server.pem",
            with_private_key=True,
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
            (EndpointSecurity.basicauth, None),
            (EndpointSecurity.wss_basicauth, self.client_cert_and_privkey),
        )
        for security, cert in username_password:
            with self.subTest(security=security):
                service = SoapServiceFactory.build(
                    url=WSDL_URI,
                    endpoint_security=security,
                    user="admin",
                    password="supersecret",
                    client_certificate=cert,
                )

                client = build_client(service)

                self.assertIsNotNone(client.transport.session.auth)

    def test_wsse(self):
        # wss endpoint security options should add a zeep.wsse.Signature
        # to the Client, so it can be used when the wsdl specifies it for a message
        # in an operation

        service = SoapServiceFactory.build(
            url=WSDL_URI,
            endpoint_security=EndpointSecurity.wss,
            client_certificate=self.client_cert_and_privkey,
        )

        client = build_client(service)

        self.assertIsInstance(client.wsse, Signature)
        self.assertIsNotNone(client.wsse.key_data)
        self.assertIsNotNone(client.wsse.cert_data)

    def test_wsse_basicauth(self):
        # wss endpoint security options should add a zeep.wsse.Signature
        # to the Client, so it can be used when the wsdl specifies it for a message
        # in an operation

        service = SoapServiceFactory.build(
            url=WSDL_URI,
            endpoint_security=EndpointSecurity.wss_basicauth,
            user="admin",
            password="supersecret",
            client_certificate=self.client_cert_and_privkey,
        )

        client = build_client(service)

        sig: Signature = next(
            extension for extension in client.wsse if isinstance(extension, Signature)
        )

        self.assertIsNotNone(sig.key_data)
        self.assertIsNotNone(sig.cert_data)

        usertoken: UsernameToken = next(
            extension
            for extension in client.wsse
            if isinstance(extension, UsernameToken)
        )

        self.assertEqual(usertoken.username, "admin")
        self.assertEqual(usertoken.password, "supersecret")

    def test_wrong_wsse(self):
        service = SoapServiceFactory.create(endpoint_security="my blue eyes")

        with self.assertRaises(ValueError):
            service.get_wsse()

    @requests_mock.Mocker()
    def test_no_absolute_url_sanitization(self, m):
        m.post("https://other-base.example.com")
        service = SoapServiceFactory.build(url=WSDL_URI)
        session_factory = SessionFactory(service)
        session = SOAPSession.configure_from(session_factory)

        try:
            with session:
                session.post("https://other-base.example.com")
        except InvalidURLError as exc:
            raise self.failureException(
                "SOAP session should not block non-base URL requests"
            ) from exc

        self.assertGreater(len(m.request_history), 0)

    @requests_mock.Mocker()
    def test_default_behaviour_relative_paths(self, m):
        m.post("https://example.com/api/relative")
        service = SoapServiceFactory.build(url="https://example.com/")
        session_factory = SessionFactory(service)
        session = SOAPSession.configure_from(session_factory)

        with session:
            session.post("api/relative")

        self.assertEqual(m.last_request.url, "https://example.com/api/relative")

    def test_it_can_build_a_functional_client(self):
        # NOTE - soapclient.com no longer exists so we can't re-record these
        # cassettes. That's not a problem, as we mostly check that the WSDL processing
        # works as expected and it's not a real service that we talk to that may break
        # our application.
        service = SoapServiceFactory.build(
            url="http://www.soapclient.com/xml/soapresponder.wsdl"
        )
        client = build_client(service)

        self.assertEqual(
            client.service.Method1("under the normal run", "things"),
            "Your input parameters are under the normal run and things",
        )


class ClientTransportTimeoutTests(TestCase):
    def test_the_client_obeys_timeout_requests(self):
        "We don't want an unresponsive service DoS us."
        service = SoapServiceFactory.build(
            # this service acts like some slow lorris, will eventually
            # respond with something that's not a wsdl
            url="https://httpstat.us/200?sleep=3000",
            timeout=1,
        )

        with self.assertRaises(RequestException):
            try:
                # zeep will try to read the "wsdl"
                build_client(service)
            except XMLSyntaxError:
                # timeout time has passed and we're trying
                self.fail("timeout not honoured by SOAP client")
