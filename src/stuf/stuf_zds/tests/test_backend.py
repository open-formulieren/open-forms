from django.test import tag

import requests_mock
from freezegun import freeze_time
from lxml import etree
from privates.test import temp_private_root
from requests import RequestException

from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.models import SubmissionStep
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
)
from soap.constants import SOAPVersion
from stuf.tests.factories import StufServiceFactory

from ..client import PaymentStatus, StufZDSClient, ZaakOptions
from ..models import StufZDSConfig
from . import StUFZDSTestBase
from .utils import load_mock, match_text, xml_from_request_history


@freeze_time("2021-10-11 11:23:00")
@temp_private_root()
@requests_mock.Mocker()
class StufZDSClientTests(StUFZDSTestBase):
    """
    test the client class directly
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = StufServiceFactory.create(
            zender_organisatie="ZenOrg",
            zender_applicatie="ZenApp",
            zender_administratie="ZenAdmin",
            zender_gebruiker="ZenUser",
            ontvanger_organisatie="OntOrg",
            ontvanger_applicatie="OntApp",
            ontvanger_administratie="OntAdmin",
            ontvanger_gebruiker="OntUser",
        )

        cls.options: ZaakOptions = {
            "omschrijving": "my-form",
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "zt-st-code",
            "zds_zaaktype_status_omschrijving": "zt-st-omschrijving",
            "zds_documenttype_omschrijving_inzending": "dt-omschrijving",
            "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
            "referentienummer": "only-here-for-typechecker",
        }

    def assertStuurgegevens(self, xml_doc):
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:zender/stuf:organisatie": "ZenOrg",
                "//zkn:stuurgegevens/stuf:zender/stuf:applicatie": "ZenApp",
                "//zkn:stuurgegevens/stuf:zender/stuf:administratie": "ZenAdmin",
                "//zkn:stuurgegevens/stuf:zender/stuf:gebruiker": "ZenUser",
                "//zkn:stuurgegevens/stuf:ontvanger/stuf:organisatie": "OntOrg",
                "//zkn:stuurgegevens/stuf:ontvanger/stuf:applicatie": "OntApp",
                "//zkn:stuurgegevens/stuf:ontvanger/stuf:administratie": "OntAdmin",
                "//zkn:stuurgegevens/stuf:ontvanger/stuf:gebruiker": "OntUser",
            },
        )

    def test_soap_12(self, m):
        self.service.soap_version = SOAPVersion.soap12
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        zaaknr = client.create_zaak_identificatie()
        self.assertEqual(zaaknr, "foo")

        request = m.request_history[0]
        self.assertEqual(request.headers["Content-Type"], "application/soap+xml")
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/genereerZaakIdentificatie_Di02",
        )

        xml = etree.fromstring(bytes(request.text, encoding="utf8"))
        soap_header = xml.xpath("/*[local-name()='Envelope']/*[local-name()='Header']")[
            0
        ]
        self.assertEqual(
            soap_header.nsmap["soapenv"], "http://www.w3.org/2003/05/soap-envelope"
        )

    def test_soap_11(self, m):
        self.service.soap_service.soap_version = SOAPVersion.soap11
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        client.create_zaak_identificatie()

        request = m.request_history[0]
        self.assertEqual(request.headers["Content-Type"], "text/xml")
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/genereerZaakIdentificatie_Di02",
        )

        xml = etree.fromstring(bytes(request.text, encoding="utf8"))
        soap_header = xml.xpath("/*[local-name()='Envelope']/*[local-name()='Header']")[
            0
        ]
        self.assertEqual(
            soap_header.nsmap["soapenv"], "http://schemas.xmlsoap.org/soap/envelope/"
        )

    def test_create_zaak_identificatie(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )

        identificatie = client.create_zaak_identificatie()

        request = m.request_history[0]
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/genereerZaakIdentificatie_Di02",
        )

        self.assertEqual(identificatie, "foo")

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathExists(xml_doc, "//zkn:genereerZaakIdentificatie_Di02")
        self.assertStuurgegevens(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerZaakidentificatie",
            },
        )

    def test_create_zaak(self, m):
        client = StufZDSClient(
            self.service,
            self.options,
            config=StufZDSConfig(zaakbetrokkene_cosigner_omschrijving="cosigner"),
        )
        self.options.update({"cosigner": "123456782"})
        m.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )

        client.create_zaak(
            "foo",
            {"bsn": "111222333", "betalings_indicatie": PaymentStatus.NOT_YET},
            {},
        )

        request = m.request_history[0]
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/creeerZaak_Lk01",
        )

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathExists(xml_doc, "//zkn:zakLk01")
        self.assertStuurgegevens(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo",
                "//zkn:object/zkn:omschrijving": "my-form",
                "//zkn:object/zkn:betalingsIndicatie": PaymentStatus.NOT_YET,
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:code": "zt-code",
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "111222333",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "123456782",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene/zkn:omschrijving": "cosigner",
            },
        )

    def test_set_zaak_payment(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),  # reuse?
            additional_matcher=match_text("zakLk01"),
        )

        client.set_zaak_payment("foo", partial=True)

        request = m.request_history[0]
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/updateZaak_Lk01",
        )

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathExists(xml_doc, "//zkn:zakLk01")
        self.assertStuurgegevens(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo",
                "//zkn:object/zkn:betalingsIndicatie": PaymentStatus.PARTIAL,
                "//zkn:object/zkn:laatsteBetaaldatum": "20211011",
            },
        )

    def test_create_document_identificatie(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml", {"document_identificatie": "bar"}
            ),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )

        identificatie = client.create_document_identificatie()

        request = m.request_history[0]
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/genereerDocumentIdentificatie_Di02",
        )

        self.assertEqual(identificatie, "bar")

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathExists(xml_doc, "//zkn:genereerDocumentIdentificatie_Di02")
        self.assertStuurgegevens(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

    def test_create_zaak_document(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(
            self.service.soap_service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        submission_report = SubmissionReportFactory.create()

        client.create_zaak_document(
            zaak_id="foo", doc_id="bar", submission_report=submission_report
        )

        request = m.request_history[0]
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/voegZaakdocumentToe_Lk01",
        )

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathExists(xml_doc, "//zkn:edcLk01")
        self.assertStuurgegevens(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "EDC",
                "//zkn:object/zkn:identificatie": "bar",
                "//zkn:object/zkn:dct.omschrijving": "dt-omschrijving",
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "open-forms-inzending.pdf",
                "//zkn:object/zkn:inhoud/@xmime:contentType": "application/pdf",
                "//zkn:object/zkn:formaat": "application/pdf",
                "//zkn:object/zkn:vertrouwelijkAanduiding": "OPENBAAR",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:identificatie": "foo",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:omschrijving": "my-form",
            },
        )

    def test_create_zaak_attachment(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(
            self.service.soap_service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        submission_attachment = SubmissionFileAttachmentFactory.create(
            file_name="my-attachment.doc",
            content_type="application/msword",
        )

        client.create_zaak_attachment(
            zaak_id="foo", doc_id="bar", submission_attachment=submission_attachment
        )
        request = m.request_history[0]
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/voegZaakdocumentToe_Lk01",
        )

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathExists(xml_doc, "//zkn:edcLk01")
        self.assertStuurgegevens(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "EDC",
                "//zkn:object/zkn:identificatie": "bar",
                "//zkn:object/zkn:dct.omschrijving": "dt-omschrijving",
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "my-attachment.doc",
                "//zkn:object/zkn:inhoud/@xmime:contentType": "application/msword",
                "//zkn:object/zkn:formaat": "application/msword",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:identificatie": "foo",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:omschrijving": "my-form",
            },
        )

    def test_create_zaak_attachment_with_custom_title(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(
            self.service.soap_service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )

        SubmissionFactory.from_components(
            [
                {
                    "key": "field1",
                    "type": "file",
                    "registration": {
                        "titel": "a custom title",
                    },
                },
            ]
        )

        submission_attachment = SubmissionFileAttachmentFactory.create(
            submission_step=SubmissionStep.objects.first(),
            file_name="my-attachment.doc",
            content_type="application/msword",
            _component_configuration_path="components.0",
        )

        client.create_zaak_attachment(
            zaak_id="foo", doc_id="bar", submission_attachment=submission_attachment
        )
        request = m.request_history[0]
        self.assertEqual(
            request.headers["SOAPAction"],
            "http://www.egem.nl/StUF/sector/zkn/0310/voegZaakdocumentToe_Lk01",
        )

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathExists(xml_doc, "//zkn:edcLk01")
        self.assertStuurgegevens(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "EDC",
                "//zkn:object/zkn:identificatie": "bar",
                "//zkn:object/zkn:dct.omschrijving": "dt-omschrijving",
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "my-attachment.doc",
                "//zkn:object/zkn:inhoud/@xmime:contentType": "application/msword",
                "//zkn:object/zkn:formaat": "application/msword",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:identificatie": "foo",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:omschrijving": "my-form",
                "//zkn:titel": "a custom title",
            },
        )

    def test_client_wraps_network_error(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(self.service.soap_service.url, exc=RequestException)
        submission_report = SubmissionReportFactory.create()

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            client.create_zaak_identificatie()

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            client.create_zaak("foo", {"bsn": "111222333"}, {})

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            client.create_document_identificatie()

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            client.create_zaak_document(
                zaak_id="foo", doc_id="bar", submission_report=submission_report
            )

    def test_client_wraps_xml_parse_error(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(self.service.soap_service.url, text="> > broken xml < <")
        submission_report = SubmissionReportFactory.create()

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            client.create_zaak_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            client.create_zaak("foo", {"bsn": "111222333"}, {})

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            client.create_document_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            client.create_zaak_document(
                zaak_id="foo", doc_id="bar", submission_report=submission_report
            )

    def test_client_wraps_bad_structure_error(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(self.service.soap_service.url, content=load_mock("dummy.xml"))

        with self.assertRaisesRegex(RegistrationFailed, r"^cannot find "):
            client.create_zaak_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^cannot find "):
            client.create_document_identificatie()

    def test_parse_error(self, m):
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        m.post(
            self.service.soap_service.url,
            status_code=500,
            content=load_mock("soap-error.xml"),
            headers={"content-type": "text/xml"},
        )

        with self.assertRaisesMessage(
            RegistrationFailed, "error while making backend request"
        ):
            client.create_zaak_identificatie()

    @tag("gh-2983", "sentry-324640")
    def test_unpack_valueerror(self, m):
        """
        Regression test where the XML response structure caused unpack errors.

        In tests this appears to be fine due to the XML structure being so that an
        element had two children(?) which could be unpacked, however in real
        integrations this appears not to be the case at all times.

        The mocked response was extracted from Celery task container logs and is kept
        exactly as it was received (including newlines, spaces...) except for
        identifying information.
        """
        client = StufZDSClient(self.service, self.options, config=StufZDSConfig())
        content_bits = (
            b"<?xml version='1.0' encoding='UTF-8'?><S:Envelope xmlns:S=\"http://schemas.xmlsoap.org/",
            b'soap/envelope/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">',
            b'<S:Body><ZKN:genereerZaakIdentificatie_Du02 xmlns:BG="http://www.egem.nl/StUF/sector/bg/0310" ',
            b'xmlns:StUF="http://www.egem.nl/StUF/StUF0301" xmlns:ZKN="http://www.egem.nl/StUF/sector/zkn/0310"',
            b' xmlns:gml="http://www.opengis.net/gml" xmlns:xlink="http://www.w3.org/1999/xlink" ',
            b'xmlns:xmime="http://www.w3.org/2005/05/xmlmime">\n   <ZKN:stuurgegevens>\n      ',
            b"<StUF:berichtcode>Du02</StUF:berichtcode>\n      <StUF:zender>\n         ",
            b"<StUF:applicatie>REDACTED</StUF:applicatie>\n      </StUF:zender>\n      <StUF:ontvanger>\n         ",
            b"<StUF:organisatie/>\n         <StUF:applicatie>REDACTED</StUF:applicatie>\n         ",
            b"<StUF:administratie/>\n         <StUF:gebruiker/>\n      </StUF:ontvanger>\n      ",
            b"<StUF:referentienummer>99999999999999999999999999999999999999</StUF:referentienummer>\n      ",
            b"<StUF:tijdstipBericht>20230413113141</StUF:tijdstipBericht>\n      ",
            b"<StUF:crossRefnummer>916bf799-38ee-45b0-b859-c2f656433e93</StUF:crossRefnummer>\n      ",
            b"<StUF:functie>genereerZaakidentificatie</StUF:functie>\n   </ZKN:stuurgegevens>\n   ",
            b'<ZKN:zaak StUF:entiteittype="ZAK" StUF:functie="entiteit">\n      ',
            b"<ZKN:identificatie>1234567</ZKN:identificatie>\n   </ZKN:zaak>\n",
            b"</ZKN:genereerZaakIdentificatie_Du02></S:Body></S:Envelope>",
        )
        m.post(self.service.soap_service.url, content=b"".join(content_bits))

        identificatie = client.create_zaak_identificatie()

        self.assertEqual(identificatie, "1234567")
