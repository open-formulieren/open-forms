"""
Test the client factory from SOAPService configuration.
"""
import unittest
from pathlib import Path

from django.test import TestCase, override_settings

import requests_mock
from ape_pie import InvalidURLError
from requests.exceptions import RequestException
from simple_certmanager.test.factories import CertificateFactory
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
            client_certificate=CertificateFactory.build(
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
        service = SoapServiceFactory.build(
            url="http://www.soapclient.com/xml/soapresponder.wsdl"
        )
        client = build_client(service)

        self.assertEqual(
            client.service.Method1("under the normal run", "things"),
            "Your input parameters are under the normal run and things",
        )

    @unittest.skip("Hangs GH CI")
    @override_settings(DEFAULT_TIMEOUT_REQUESTS=1)
    def test_the_client_obeys_timeout_requests(self):
        "We don't want an unresponsive service DoS us."
        # Rig the cassette for failure
        # import signal
        # from time import sleep
        # self.cassette.play_response = lambda request: sleep(2)
        # self.cassette.can_play_response_for = lambda request: True
        self.cassette.record_mode = "all"

        service = SoapServiceFactory.build(
            # this service acts like some slow lorris on https
            url="https://www.soapclient.com/xml/soapresponder.wsdl"
        )

        # signals aren't thread save
        org_handler = signal.getsignal(signal.SIGALRM)
        self.addCleanup(lambda: signal.signal(signal.SIGALRM, org_handler))
        signal.signal(
            signal.SIGALRM,
            lambda _sig, _frm: self.fail("Client seems to hang")
            # but there is a chance be that the service started responding, but we couldn't
            # process the wsdl in time
        )
        with self.assertRaises(RequestException):
            signal.alarm(5)
            # zeep will try to read the wsdl
            build_client(service)

            # Passed this point, the test has broken, find or create another test service
            # that opens the socket, but doesn't respond.
            self.fail("The service unexpectedly responded!")
