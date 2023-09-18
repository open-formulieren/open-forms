from django.core.files import File
from django.test import TestCase, tag

import requests_mock
from privates.test import temp_private_root
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.models import Certificate

from openforms.utils.tests.logging import disable_logging

from ..client import QmaticClient
from .utils import TEST_FILES, MockConfigMixin

CLIENT_CERTIFICATE = TEST_FILES / "test.certificate"
CLIENT_KEY = TEST_FILES / "test.key"


@temp_private_root()
@tag("gh-3328")
@disable_logging()
class ClientMutualTLSTests(MockConfigMixin, TestCase):
    maxDiff = 1024
    api_root: str

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # type: ignore

        with CLIENT_CERTIFICATE.open("rb") as cert_file, CLIENT_KEY.open(
            "rb"
        ) as key_file:
            cls.client_cert = Certificate.objects.create(
                label="Gateway client certificate",
                type=CertificateTypes.key_pair,
                public_certificate=File(cert_file, "client.pem"),
                private_key=File(key_file, "client_key.pem"),
            )
            cls.server_cert = Certificate.objects.create(
                label="Gateway server certificate",
                type=CertificateTypes.cert_only,
                public_certificate=File(cert_file, "server.pem"),
            )

        cls.service.client_certificate = cls.client_cert
        cls.service.server_certificate = cls.server_cert
        cls.service.save()

    def test_client_supports_mtls(self):
        server_cert_path = self.server_cert.public_certificate.path

        client = QmaticClient()

        self.assertEqual(client.verify, server_cert_path)

    @requests_mock.Mocker()
    def test_api_call_offers_client_cert(self, m):
        m.get(requests_mock.ANY)
        client = QmaticClient()

        with client:
            client.get(self.service.api_root)

        self.assertEqual(len(m.request_history), 1)
        self.assertEqual(
            m.last_request.cert,
            (
                self.client_cert.public_certificate.path,
                self.client_cert.private_key.path,
            ),
        )
