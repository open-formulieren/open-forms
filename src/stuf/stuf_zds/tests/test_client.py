from pathlib import Path
from unittest import skipIf
from unittest.mock import patch

from django.core.files import File
from django.template.loader import render_to_string
from django.test import TestCase, tag

import requests_mock
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.models import Certificate

from openforms.registrations.exceptions import RegistrationFailed
from openforms.tests.utils import can_connect
from stuf.constants import EndpointType

from ...tests.factories import StufServiceFactory
from ..client import StufZDSClient

TEST_CERTIFICATES = Path(__file__).parent.parent.parent / "tests" / "data"


@requests_mock.Mocker()
class StufZdsClientTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        certificate_file = TEST_CERTIFICATES / "test.certificate"
        key_file = TEST_CERTIFICATES / "test.key"

        with key_file.open("r") as key_f, certificate_file.open("r") as certificate_f:
            cls.client_certificate = Certificate.objects.create(
                label="Test client certificate",
                type=CertificateTypes.key_pair,
                public_certificate=File(certificate_f, name="test.certificate"),
                private_key=File(key_f, name="test.key"),
            )
            cls.client_certificate_only = Certificate.objects.create(
                label="Test client certificate (only cert)",
                type=CertificateTypes.cert_only,
                public_certificate=File(certificate_f, name="test1.certificate"),
            )
            cls.server_certificate = Certificate.objects.create(
                label="Test server certificate",
                type=CertificateTypes.cert_only,
                public_certificate=File(certificate_f, name="test2.certificate"),
            )

        cls.client_options = {
            "gemeentecode": "1234",
            "omschrijving": "my-form",
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "zt-st-code",
            "zds_zaaktype_status_omschrijving": "zt-st-omschrijving",
            "zds_documenttype_omschrijving_inzending": "dt-omschrijving",
            "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
        }

    def test_mutual_tls(self, m):
        stuf_service = StufServiceFactory.create(
            soap_service__client_certificate=self.client_certificate,
            soap_service__server_certificate=self.server_certificate,
        )

        m.post(
            stuf_service.soap_service.url,
            text=render_to_string("stuf_zds/soap/creeerZaak.xml"),
        )

        client = StufZDSClient(stuf_service, self.client_options)

        client.create_zaak(zaak_identificatie="ZAAK-01", zaak_data={}, extra_data={})

        history = m.request_history
        request_with_tls = history[-1]

        self.assertEqual(
            self.server_certificate.public_certificate.path, request_with_tls.verify
        )
        self.assertEqual(
            (
                self.client_certificate.public_certificate.path,
                self.client_certificate.private_key.path,
            ),
            request_with_tls.cert,
        )

    def test_mutual_tls_no_private_key(self, m):
        stuf_service = StufServiceFactory.create(
            soap_service__client_certificate=self.client_certificate_only,
            soap_service__server_certificate=self.server_certificate,
        )

        m.post(
            stuf_service.soap_service.url,
            text=render_to_string("stuf_zds/soap/creeerZaak.xml"),
        )

        client = StufZDSClient(stuf_service, self.client_options)

        client.create_zaak(zaak_identificatie="ZAAK-01", zaak_data={}, extra_data={})

        history = m.request_history
        request_with_tls = history[-1]

        self.assertEqual(
            self.server_certificate.public_certificate.path, request_with_tls.verify
        )
        self.assertEqual(
            self.client_certificate_only.public_certificate.path,
            request_with_tls.cert,
        )

    def test_no_mutual_tls(self, m):
        stuf_service = StufServiceFactory.create()

        m.post(
            stuf_service.soap_service.url,
            text=render_to_string("stuf_zds/soap/creeerZaak.xml"),
        )

        client = StufZDSClient(stuf_service, self.client_options)

        client.create_zaak(zaak_identificatie="ZAAK-01", zaak_data={}, extra_data={})

        history = m.request_history
        request_with_tls = history[-1]

        self.assertTrue(request_with_tls.verify)
        self.assertEqual(
            (None, None),
            request_with_tls.cert,
        )


class StufZdsRegressionTests(TestCase):
    @tag("gh-1731")
    @skipIf(not can_connect("example.com:443"), "Need real socket/connection for test")
    def test_non_latin1_characters(self):
        """
        Regression test for non-latin1 characters in the XML body.

        We cannot mock the calls using requests_mock here as the crash happens inside
        http.client, used by requests.
        """
        stuf_service = StufServiceFactory.create()
        client = StufZDSClient(stuf_service, {})

        with patch.object(
            client.service, "get_endpoint", return_value="https://example.com"
        ):
            try:
                client._make_request(
                    template_name="stuf_zds/soap/creeerZaak.xml",
                    context={"referentienummer": "123", "extra": {"foo": "Ş"}},
                    endpoint_type=EndpointType.ontvang_asynchroon,
                )
            except UnicodeError:
                self.fail("Body encoding should succeed")
            except RegistrationFailed:
                pass
