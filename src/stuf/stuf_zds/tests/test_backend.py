import uuid

from django.template import loader
from django.test import TestCase

import requests_mock
from freezegun import freeze_time
from lxml import etree
from lxml.etree import ElementTree
from privates.test import temp_private_root
from requests import RequestException

from openforms.logging.models import TimelineLogProxy
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.tests.factories import (
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
)
from stuf.constants import SOAPVersion
from stuf.tests.factories import StufServiceFactory

from ..client import PaymentStatus, StufZDSClient, nsmap


def load_mock(name, context=None):
    return loader.render_to_string(
        f"stuf_zds/soap/response-mock/{name}", context
    ).encode("utf8")


def match_text(text):
    # requests_mock matcher for SOAP requests
    def _matcher(request):
        return text in (request.text or "")

    return _matcher


def xml_from_request_history(m, index) -> ElementTree:
    request = m.request_history[index]
    xml = etree.fromstring(bytes(request.text, encoding="utf8"))
    return xml


class StufTestBase(TestCase):
    namespaces = nsmap

    def assertXPathExists(self, xml_doc, xpath):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        if len(elements) == 0:
            self.fail(f"cannot find XML element(s) with xpath {xpath}")

    def assertXPathNotExists(self, xml_doc, xpath):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        if len(elements) != 0:
            self.fail(
                f"found {len(elements)} unexpected XML element(s) with xpath {xpath}"
            )

    def assertXPathCount(self, xml_doc, xpath, count):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        self.assertEqual(
            len(elements),
            count,
            f"cannot find exactly {count} XML element(s) with xpath {xpath}",
        )

    def assertXPathEquals(self, xml_doc, xpath, text):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        self.assertGreaterEqual(
            len(elements), 1, f"cannot find XML element(s) with xpath {xpath}"
        )
        self.assertEqual(
            len(elements), 1, f"multiple XML element(s) found for xpath {xpath}"
        )
        if isinstance(elements[0], str):
            self.assertEqual(elements[0].strip(), text, f"at xpath {xpath}")
        else:
            elem_text = elements[0].text
            if elem_text is None:
                elem_text = ""
            else:
                elem_text = elem_text.strip()
            self.assertEqual(elem_text, text, f"at xpath {xpath}")

    def assertXPathEqualDict(self, xml_doc, path_value_dict):
        for path, value in path_value_dict.items():
            self.assertXPathEquals(xml_doc, path, value)

    def assertSoapXMLCommon(self, xml_doc):
        self.assertIsNotNone(xml_doc)
        self.assertXPathExists(
            xml_doc, "/*[local-name()='Envelope']/*[local-name()='Header']"
        )
        self.assertXPathExists(
            xml_doc, "/*[local-name()='Envelope']/*[local-name()='Body']"
        )


@freeze_time("2021-10-11 11:23:00")
@temp_private_root()
@requests_mock.Mocker()
class StufZDSClientTests(StufTestBase):
    """
    test the client class directly
    """

    def setUp(self):
        self.service = StufServiceFactory.create(
            zender_organisatie="ZenOrg",
            zender_applicatie="ZenApp",
            zender_administratie="ZenAdmin",
            zender_gebruiker="ZenUser",
            ontvanger_organisatie="OntOrg",
            ontvanger_applicatie="OntApp",
            ontvanger_administratie="OntAdmin",
            ontvanger_gebruiker="OntUser",
        )

        self.options = {
            "gemeentecode": "1234",
            "omschrijving": "my-form",
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "zt-st-code",
            "zds_zaaktype_status_omschrijving": "zt-st-omschrijving",
            "zds_documenttype_omschrijving_inzending": "dt-omschrijving",
            "referentienummer": str(uuid.uuid4()),
        }
        self.client = StufZDSClient(self.service, self.options)

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
        self.service.save()

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
        self.client.create_zaak_identificatie()

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

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            1,
        )

    def test_soap_11(self, m):
        self.service.soap_service.soap_version = SOAPVersion.soap11
        self.service.save()

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
        self.client.create_zaak_identificatie()

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

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            1,
        )

    def test_create_zaak_identificatie(self, m):
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

        identificatie = self.client.create_zaak_identificatie()

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

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            1,
        )

    def test_create_zaak(self, m):
        m.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )

        self.client.create_zaak("foo", {"bsn": "111222333"}, {}, payment_required=True)

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
            },
        )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            1,
        )

    def test_set_zaak_payment(self, m):
        m.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),  # reuse?
            additional_matcher=match_text("zakLk01"),
        )

        self.client.set_zaak_payment("foo", partial=True)

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

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            1,
        )

    def test_create_document_identificatie(self, m):
        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml", {"document_identificatie": "bar"}
            ),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )

        identificatie = self.client.create_document_identificatie()

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

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            1,
        )

    def test_create_zaak_document(self, m):
        m.post(
            self.service.soap_service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        submission_report = SubmissionReportFactory.create()

        self.client.create_zaak_document(
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
                "//zkn:object/zkn:formaat": "application/pdf",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:identificatie": "foo",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:omschrijving": "my-form",
            },
        )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            1,
        )

    def test_create_zaak_attachment(self, m):
        m.post(
            self.service.soap_service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        submission_attachment = SubmissionFileAttachmentFactory.create(
            file_name="my-attachment.doc",
            content_type="application/msword",
        )

        self.client.create_zaak_attachment(
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
                "//zkn:object/zkn:formaat": "application/msword",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:identificatie": "foo",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:omschrijving": "my-form",
            },
        )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            1,
        )

    def test_client_wraps_network_error(self, m):
        m.post(self.service.soap_service.url, exc=RequestException)
        submission_report = SubmissionReportFactory.create()

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            self.client.create_zaak_identificatie()

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            self.client.create_zaak("foo", {"bsn": "111222333"}, {})

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            self.client.create_document_identificatie()

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            self.client.create_zaak_document(
                zaak_id="foo", doc_id="bar", submission_report=submission_report
            )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            4,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_failure_response.txt"
            ).count(),
            4,
        )

    def test_client_wraps_xml_parse_error(self, m):
        m.post(self.service.soap_service.url, text="> > broken xml < <")
        submission_report = SubmissionReportFactory.create()

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            self.client.create_zaak_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            self.client.create_zaak("foo", {"bsn": "111222333"}, {})

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            self.client.create_document_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            self.client.create_zaak_document(
                zaak_id="foo", doc_id="bar", submission_report=submission_report
            )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            4,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_failure_response.txt"
            ).count(),
            4,
        )

    def test_client_wraps_bad_structure_error(self, m):
        m.post(self.service.soap_service.url, content=load_mock("dummy.xml"))

        with self.assertRaisesRegex(RegistrationFailed, r"^cannot find "):
            self.client.create_zaak_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^cannot find "):
            self.client.create_document_identificatie()

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            2,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            2,
        )

    def test_parse_error(self, m):
        m.post(
            self.service.soap_service.url,
            status_code=500,
            content=load_mock("soap-error.xml"),
            headers={"content-type": "text/xml"},
        )

        with self.assertRaisesMessage(
            RegistrationFailed, "error while making backend request"
        ):
            self.client.create_zaak_identificatie()

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            1,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_failure_response.txt"
            ).count(),
            1,
        )
