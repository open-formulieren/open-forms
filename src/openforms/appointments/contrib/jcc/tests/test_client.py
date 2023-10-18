from unittest.mock import patch

from django.test import TestCase

from privates.test import temp_private_root
from simple_certmanager.test.factories import CertificateFactory
from zeep.client import Client as ZeepClient

from soap.tests.factories import SoapServiceFactory

from ..client import get_client
from ..models import JccConfig
from .utils import WSDL


@temp_private_root()
class ClientConfigurationTests(TestCase):
    @patch("openforms.appointments.contrib.jcc.client.JccConfig.get_solo")
    def test_client_transport_supports_mtls(self, m_get_solo):
        # Smoke test to check that the service configuration is honoured
        client_cert = CertificateFactory.create(with_private_key=True)
        config = JccConfig(
            service=SoapServiceFactory.build(
                url=WSDL,  # cheat by passing a file path
                client_certificate=client_cert,
            )
        )
        m_get_solo.return_value = config

        client = get_client()

        self.assertIsInstance(client, ZeepClient)
        self.assertEqual(
            client.transport.session.cert,
            (client_cert.public_certificate.path, client_cert.private_key.path),
        )
