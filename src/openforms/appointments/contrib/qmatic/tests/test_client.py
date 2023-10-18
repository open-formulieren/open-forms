from django.test import TestCase, tag

import requests_mock
from privates.test import temp_private_root
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.test.factories import CertificateFactory

from openforms.utils.tests.logging import disable_logging

from ..client import QmaticClient
from .utils import MockConfigMixin


@temp_private_root()
@tag("gh-3328")
@disable_logging()
class ClientMutualTLSTests(MockConfigMixin, TestCase):
    maxDiff = 1024
    api_root: str

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # type: ignore

        cls.client_cert = CertificateFactory.create(
            label="Gateway client certificate",
            public_certificate__filename="client.pem",
            with_private_key=True,
            private_key__filename="client_key.pem",
        )
        cls.server_cert = CertificateFactory.create(
            label="Gateway server certificate",
            type=CertificateTypes.cert_only,
            public_certificate__filename="server.pem",
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
