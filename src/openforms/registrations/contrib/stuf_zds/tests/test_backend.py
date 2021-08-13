import dataclasses
import uuid
from unittest.mock import patch

from django.template import loader
from django.test import TestCase

import requests_mock
from lxml import etree
from lxml.etree import ElementTree
from privates.test import temp_private_root
from requests import RequestException

from openforms.registrations.constants import RegistrationAttribute
from openforms.registrations.contrib.stuf_zds.client import StufZDSClient, nsmap
from openforms.registrations.contrib.stuf_zds.models import StufZDSConfig
from openforms.registrations.contrib.stuf_zds.plugin import (
    PartialDate,
    StufZDSRegistration,
)
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
)
from stuf.constants import SOAPVersion
from stuf.tests.factories import SoapServiceFactory


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


class StufZDSHelperTests(StufTestBase):
    def test_partial_date(self):
        # good
        actual = PartialDate.parse("2020-01-01")
        self.assertEqual(dict(year=2020, month=1, day=1), dataclasses.asdict(actual))
        self.assertEqual("20200101", actual.value)
        self.assertEqual("V", actual.indicator)

        actual = PartialDate.parse("2020-01")
        self.assertEqual(dict(year=2020, month=1, day=None), dataclasses.asdict(actual))
        self.assertEqual("202001", actual.value)
        self.assertEqual("D", actual.indicator)

        actual = PartialDate.parse("2020")
        self.assertEqual(
            dict(year=2020, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("2020", actual.value)
        self.assertEqual("M", actual.indicator)

        actual = PartialDate.parse("")
        self.assertEqual(
            dict(year=None, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("", actual.value)
        self.assertEqual("J", actual.indicator)

        # partial zeros
        actual = PartialDate.parse("2020-01-00")
        self.assertEqual(dict(year=2020, month=1, day=None), dataclasses.asdict(actual))
        self.assertEqual("202001", actual.value)
        self.assertEqual("D", actual.indicator)

        actual = PartialDate.parse("2020-00-00")
        self.assertEqual(
            dict(year=2020, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("2020", actual.value)
        self.assertEqual("M", actual.indicator)

        actual = PartialDate.parse("2020-00")
        self.assertEqual(
            dict(year=2020, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("2020", actual.value)
        self.assertEqual("M", actual.indicator)

        # full zeros
        actual = PartialDate.parse("0000")
        self.assertEqual(
            dict(year=None, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("", actual.value)
        self.assertEqual("J", actual.indicator)

        actual = PartialDate.parse("0000-00-00")
        self.assertEqual(
            dict(year=None, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("", actual.value)
        self.assertEqual("J", actual.indicator)

        actual = PartialDate.parse("0-0-0")
        self.assertEqual(
            dict(year=None, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("", actual.value)
        self.assertEqual("J", actual.indicator)

        actual = PartialDate.parse("0-0")
        self.assertEqual(
            dict(year=None, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("", actual.value)
        self.assertEqual("J", actual.indicator)

        actual = PartialDate.parse("0")
        self.assertEqual(
            dict(year=None, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("", actual.value)
        self.assertEqual("J", actual.indicator)

        # bad
        actual = PartialDate.parse(None)
        self.assertEqual(
            dict(year=None, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("", actual.value)
        self.assertEqual("J", actual.indicator)

        actual = PartialDate.parse("20202-01-01")
        self.assertEqual(
            dict(year=None, month=None, day=None), dataclasses.asdict(actual)
        )
        self.assertEqual("", actual.value)
        self.assertEqual("J", actual.indicator)


@temp_private_root()
@requests_mock.Mocker()
class StufZDSClientTests(StufTestBase):
    """
    test the client class directly
    """

    def setUp(self):
        self.service = SoapServiceFactory(
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
            "zds_documenttype_omschrijving": "dt-omschrijving",
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
            self.service.url,
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

        self.assertEqual(request.headers.get("Content-Type"), "application/soap+xml")
        xml = etree.fromstring(bytes(request.text, encoding="utf8"))
        soap_header = xml.xpath("/*[local-name()='Envelope']/*[local-name()='Header']")[
            0
        ]
        self.assertEqual(
            soap_header.nsmap["soapenv"], "http://www.w3.org/2003/05/soap-envelope"
        )

    def test_soap_11(self, m):
        self.service.soap_version = SOAPVersion.soap11
        self.service.save()

        m.post(
            self.service.url,
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

        self.assertEqual(request.headers.get("Content-Type"), "text/xml")
        xml = etree.fromstring(bytes(request.text, encoding="utf8"))
        soap_header = xml.xpath("/*[local-name()='Envelope']/*[local-name()='Header']")[
            0
        ]
        self.assertEqual(
            soap_header.nsmap["soapenv"], "http://schemas.xmlsoap.org/soap/envelope/"
        )

    def test_create_zaak_identificatie(self, m):
        m.post(
            self.service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )

        identificatie = self.client.create_zaak_identificatie()

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
        m.post(
            self.service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )

        self.client.create_zaak("foo", {"bsn": "111222333"}, {})

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
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:code": "zt-code",
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "111222333",
            },
        )

    def test_create_document_identificatie(self, m):
        m.post(
            self.service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml", {"document_identificatie": "bar"}
            ),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )

        identificatie = self.client.create_document_identificatie()

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
        m.post(
            self.service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        submission_report = SubmissionReportFactory.create()

        self.client.create_zaak_document(
            zaak_id="foo", doc_id="bar", submission_report=submission_report
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

    def test_create_zaak_attachment(self, m):
        m.post(
            self.service.url,
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

    def test_client_wraps_network_error(self, m):
        m.post(self.service.url, exc=RequestException)
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

    def test_client_wraps_xml_parse_error(self, m):
        m.post(self.service.url, text="> > broken xml < <")
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

    def test_client_wraps_bad_structure_error(self, m):
        m.post(self.service.url, content=load_mock("dummy.xml"))

        with self.assertRaisesRegex(RegistrationFailed, r"^cannot find "):
            self.client.create_zaak_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^cannot find "):
            self.client.create_document_identificatie()

    def test_parse_error(self, m):
        m.post(
            self.service.url,
            status_code=500,
            content=load_mock("soap-error.xml"),
            headers={"content-type": "text/xml"},
        )

        with self.assertRaisesMessage(
            RegistrationFailed, "error while making backend request"
        ):
            self.client.create_zaak_identificatie()


@temp_private_root()
@requests_mock.Mocker()
class StufZDSPluginTests(StufTestBase):
    """
    test the plugin function
    """

    def setUp(self):
        self.service = SoapServiceFactory.create()
        config = StufZDSConfig.get_solo()
        config.service = self.service
        config.save()

    @patch("celery.app.task.Task.request")
    def test_plugin(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geboortedatum,
                    },
                },
                {
                    "key": "extra",
                },
            ],
            form__name="my-form",
            bsn="111222333",
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
                "extra": "BuzzBazz",
            },
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
        )

        m.post(
            self.service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo-zaak",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        m.post(
            self.service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )

        m.post(
            self.service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml",
                {"document_identificatie": "bar-document"},
            ),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )

        m.post(
            self.service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        mock_task.id = 1

        form_options = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
        }

        plugin = StufZDSRegistration("stuf")
        registration_id, result = plugin.register_submission(submission, form_options)
        self.assertEqual(
            result,
            {
                "zaak": "foo-zaak",
                "document": "bar-document",
            },
        )
        self.assertEqual(registration_id, "foo-zaak")

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)

        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo-zaak",
                "//zkn:object/zkn:omschrijving": "my-form",
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:code": "zt-code",
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "111222333",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Foo",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Bar",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "de",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20001231",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum/@stuf:indOnvolledigeDatum": "V",
            },
        )
        # extraElementen
        self.assertXPathEquals(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='extra']",
            "BuzzBazz",
        )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 2)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "open-forms-inzending.pdf",
                "//zkn:object/zkn:formaat": "application/pdf",
            },
        )

        # attachment
        xml_doc = xml_from_request_history(m, 4)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 5)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "my-attachment.doc",
                "//zkn:object/zkn:formaat": "application/msword",
            },
        )
