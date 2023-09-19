from pathlib import Path

from django.core.files import File
from django.test import TestCase

import requests_mock
from privates.test import temp_private_root
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.models import Certificate
from zgw_consumers.constants import AuthTypes

from api_client import APIClient

from ..api_client import ServiceClientFactory
from ..factories import ServiceFactory

TEST_FILES = Path(__file__).parent.resolve() / "data"

CLIENT_CERTIFICATE = TEST_FILES / "test.certificate"
CLIENT_KEY = TEST_FILES / "test.key"


@temp_private_root()
class ClientFromServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        with CLIENT_CERTIFICATE.open("rb") as cert_file, CLIENT_KEY.open(
            "rb"
        ) as key_file:
            cls.client_cert_only = Certificate.objects.create(
                label="Gateway client certificate",
                type=CertificateTypes.cert_only,
                public_certificate=File(cert_file, "client_cert.pem"),
            )
            cls.client_cert_and_privkey = Certificate.objects.create(
                label="Gateway client certificate",
                type=CertificateTypes.key_pair,
                public_certificate=File(cert_file, "client_cert.pem"),
                private_key=File(key_file, "client_key.pem"),
            )
            cls.server_cert = Certificate.objects.create(
                label="Gateway server certificate",
                type=CertificateTypes.cert_only,
                public_certificate=File(cert_file, "server.pem"),
            )

    def test_no_server_cert_specified(self):
        service = ServiceFactory.build()
        factory = ServiceClientFactory(service)

        client = APIClient.configure_from(factory)

        self.assertIs(client.verify, True)  # not just truthy, but identity check

    def test_server_cert_specified(self):
        service = ServiceFactory.build(server_certificate=self.server_cert)
        factory = ServiceClientFactory(service)

        client = APIClient.configure_from(factory)

        self.assertEqual(client.verify, self.server_cert.public_certificate.path)

    def test_no_client_cert_specified(self):
        service = ServiceFactory.build()
        factory = ServiceClientFactory(service)

        client = APIClient.configure_from(factory)

        self.assertIsNone(client.cert)

    def test_client_cert_only_public_cert_specified(self):
        service = ServiceFactory.build(client_certificate=self.client_cert_only)
        factory = ServiceClientFactory(service)

        client = APIClient.configure_from(factory)

        self.assertEqual(client.cert, self.client_cert_only.public_certificate.path)

    def test_client_cert_public_cert_and_privkey_specified(self):
        service = ServiceFactory.build(client_certificate=self.client_cert_and_privkey)
        factory = ServiceClientFactory(service)

        client = APIClient.configure_from(factory)

        self.assertEqual(
            client.cert,
            (
                self.client_cert_and_privkey.public_certificate.path,
                self.client_cert_and_privkey.private_key.path,
            ),
        )

    def test_no_auth(self):
        service = ServiceFactory.build(auth_type=AuthTypes.no_auth)
        factory = ServiceClientFactory(service)

        client = APIClient.configure_from(factory)

        self.assertIsNone(client.auth)

    def test_api_key_auth(self):
        service = ServiceFactory.build(
            api_root="https://example.com/",
            auth_type=AuthTypes.api_key,
            header_key="Some-Auth-Header",
            header_value="some-api-key",
        )
        factory = ServiceClientFactory(service)
        client = APIClient.configure_from(factory)

        with self.subTest("client.auth configuration"):
            self.assertIsNotNone(client.auth)

        with self.subTest("dummy API call"):
            with requests_mock.Mocker() as m, client:
                m.get("https://example.com/foo")

                client.get("foo")

            headers = m.last_request.headers
            self.assertIn("Some-Auth-Header", headers)
            self.assertEqual(headers["Some-Auth-Header"], "some-api-key")

    def test_zgw_auth(self):
        service = ServiceFactory.build(
            api_root="https://example.com/",
            auth_type=AuthTypes.zgw,
            client_id="my-client-id",
            secret="my-secret",
        )
        factory = ServiceClientFactory(service)
        client = APIClient.configure_from(factory)

        with self.subTest("client.auth configuration"):
            self.assertIsNotNone(client.auth)

        with self.subTest("dummy API call"):
            with requests_mock.Mocker() as m, client:
                m.get("https://example.com/foo")

                client.get("foo")

            headers = m.last_request.headers
            self.assertIn("Authorization", headers)
            self.assertTrue(headers["Authorization"].startswith("Bearer "))
