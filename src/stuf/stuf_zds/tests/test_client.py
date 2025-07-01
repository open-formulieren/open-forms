from unittest import skipIf
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, tag

import requests_mock
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.test.factories import CertificateFactory

from openforms.logging.tests.utils import disable_timelinelog
from openforms.registrations.exceptions import RegistrationFailed
from openforms.tests.utils import can_connect

from ...constants import EndpointType
from ...tests.factories import StufServiceFactory
from ..client import StufZDSClient, ZaakOptions
from ..models import StufZDSConfig


@requests_mock.Mocker()
class StufZdsClientTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.client_certificate = CertificateFactory.create(
            label="Test client certificate",
            with_private_key=True,
        )
        cls.client_certificate_only = CertificateFactory.create(
            label="Test client certificate (only cert)",
            type=CertificateTypes.cert_only,
            public_certificate__filename="test1.certificate",
        )
        cls.server_certificate = CertificateFactory.create(
            label="Test server certificate",
            type=CertificateTypes.cert_only,
            public_certificate__filename="test1.certificate",
        )

        cls.client_options: ZaakOptions = {
            "omschrijving": "my-form",
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "zt-st-code",
            "zds_zaaktype_status_omschrijving": "zt-st-omschrijving",
            "zds_documenttype_omschrijving_inzending": "dt-omschrijving",
            "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
            "referentienummer": "only-here-for-typechecker",
        }

    def test_mutual_tls(self, m):
        stuf_service = StufServiceFactory.create(
            soap_service__client_certificate=self.client_certificate,
            soap_service__server_certificate=self.server_certificate,
        )
        client = StufZDSClient(
            stuf_service, self.client_options, config=StufZDSConfig()
        )
        m.post(
            stuf_service.soap_service.url,
            text=render_to_string(
                "stuf_zds/soap/creeerZaak.xml", context=client.build_base_context()
            ),
        )

        client.create_zaak(zaak_identificatie="ZAAK-01", zaak_data={}, extra_data={})

        request_with_tls = m.last_request

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
        client = StufZDSClient(
            stuf_service, self.client_options, config=StufZDSConfig()
        )
        m.post(
            stuf_service.soap_service.url,
            text=render_to_string(
                "stuf_zds/soap/creeerZaak.xml", context=client.build_base_context()
            ),
        )

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
        client = StufZDSClient(
            stuf_service, self.client_options, config=StufZDSConfig()
        )
        m.post(
            stuf_service.soap_service.url,
            text=render_to_string(
                "stuf_zds/soap/creeerZaak.xml", context=client.build_base_context()
            ),
        )

        client.create_zaak(zaak_identificatie="ZAAK-01", zaak_data={}, extra_data={})

        history = m.request_history
        request_with_tls = history[-1]

        self.assertTrue(request_with_tls.verify)
        self.assertIsNone(request_with_tls.cert)


@disable_timelinelog()
class StufZdsRegressionTests(SimpleTestCase):
    @tag("gh-1731")
    @skipIf(not can_connect("example.com:443"), "Need real socket/connection for test")
    def test_non_latin1_characters(self):
        """
        Regression test for non-latin1 characters in the XML body.

        We cannot mock the calls using requests_mock here as the crash happens inside
        http.client, used by requests.
        """
        stuf_service = StufServiceFactory.build()
        client = StufZDSClient(
            stuf_service,
            {},  # pyright: ignore[reportArgumentType]
            config=StufZDSConfig(),
        )

        with patch.object(
            client, "to_absolute_url", return_value="https://example.com"
        ):
            context = {
                **client.build_base_context(),
                "referentienummer": "123",
                "extra": {"foo": "Ş"},
            }
            try:
                client.templated_request(
                    soap_action="irrelevant",
                    template="stuf_zds/soap/creeerZaak.xml",
                    context=context,
                    endpoint_type=EndpointType.ontvang_asynchroon,
                )
            except UnicodeError:
                self.fail("Body encoding should succeed")
            except RegistrationFailed:
                pass

    @tag("gh-4146")
    @requests_mock.Mocker()
    def test_custom_timeout_applied(self, m: requests_mock.Mocker):
        m.get("https://example.com/path", text="ok")
        stuf_service = StufServiceFactory.build(
            soap_service__url="https://example.com", soap_service__timeout=1
        )
        with StufZDSClient(
            stuf_service,
            {},  # pyright: ignore[reportArgumentType]
            config=StufZDSConfig(),
        ) as client:
            client.get("https://example.com/path")

        assert m.last_request.timeout == 1  # type: ignore
