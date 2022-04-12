import os

from django.conf import settings
from django.core.files import File
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import TestCase

import requests_mock
from zgw_consumers.constants import CertificateTypes
from zgw_consumers.models import Certificate

from ...tests.factories import StufServiceFactory
from ..client import StufZDSClient

TEST_CERTIFICATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TEST_XML = os.path.join(
    settings.BASE_DIR,
    "src",
    "stuf",
    "stuf_zds",
    "templates",
    "stuf_zds",
    "soap",
)


@requests_mock.Mocker()
class StufZdsClientTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        with open(
            os.path.join(TEST_CERTIFICATES, "test.certificate"), "r"
        ) as certificate_f:
            with open(os.path.join(TEST_CERTIFICATES, "test.key"), "r") as key_f:
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
            "referentienummer": "123-123-123",
        }

    def test_mutual_tls(self, m):
        stuf_service = StufServiceFactory.create(
            soap_service__client_certificate=self.client_certificate,
            soap_service__server_certificate=self.server_certificate,
        )

        m.post(
            stuf_service.soap_service.url,
            content=render_to_string(os.path.join(TEST_XML, "creeerZaak.xml")).encode(
                "utf-8"
            ),
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

        with open(os.path.join(TEST_XML, "creeerZaak.xml"), "r") as f:
            m.post(
                stuf_service.soap_service.url,
                content=Template(f.read()).render(Context({})).encode("utf-8"),
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

        with open(os.path.join(TEST_XML, "creeerZaak.xml"), "r") as f:
            m.post(
                stuf_service.soap_service.url,
                content=Template(f.read()).render(Context({})).encode("utf-8"),
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
