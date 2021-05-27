import uuid

from django.template import loader
from django.test import TestCase

import requests_mock
from lxml import etree
from requests import RequestException

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.registrations.contrib.stuf_zds.client import StufZDSClient, nsmap
from openforms.registrations.contrib.stuf_zds.models import StufZDSConfig
from openforms.registrations.contrib.stuf_zds.plugin import create_zaak_plugin
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
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


def xml_from_request_history(m, index):
    request = m.request_history[index]
    xml = etree.fromstring(bytes(request.text, encoding="utf8"))
    return xml


class StufTestBase(TestCase):
    namespaces = nsmap

    def assertXPathExists(self, xml_doc, xpath):
        elements = xml_doc.xpath(xpath, namespaces=self.namespaces)
        if len(elements) == 0:
            self.fail(f"cannot find XML element(s) with xpath {xpath}")

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
        self.assertXPathExists(xml_doc, "/soapenv:Envelope/soapenv:Header")
        self.assertXPathExists(xml_doc, "/soapenv:Envelope/soapenv:Body")


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

        self.client.create_zaak("foo", {"bsn": "111222333"})

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
            additional_matcher=match_text("voegZaakdocumentToe_EdcLk01"),
        )

        self.client.create_zaak_document(zaak_id="foo", doc_id="bar", body="bazz")

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathExists(xml_doc, "//zds:voegZaakdocumentToe_EdcLk01")
        self.assertStuurgegevens(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "EDC",
                "//zkn:object/zkn:identificatie": "bar",
                "//zkn:object/zkn:dct.omschrijving": "my-form",
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "file-bar.b64.txt",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:identificatie": "foo",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:omschrijving": "my-form",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:isVan/zkn:gerelateerde/zkn:code": "zt-code",
                "//zkn:object/zkn:isRelevantVoor/zkn:gerelateerde/zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
            },
        )

    def test_client_wraps_network_error(self, m):
        m.post(self.service.url, exc=RequestException)

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            self.client.create_zaak_identificatie()

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            self.client.create_zaak("foo", {"bsn": "111222333"})

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            self.client.create_document_identificatie()

        with self.assertRaisesRegex(
            RegistrationFailed, r"^error while making backend "
        ):
            self.client.create_zaak_document(zaak_id="foo", doc_id="bar", body="bazz")

    def test_client_wraps_xml_parse_error(self, m):
        m.post(self.service.url, text="> > broken xml < <")

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            self.client.create_zaak_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            self.client.create_zaak("foo", {"bsn": "111222333"})

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            self.client.create_document_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^error while parsing "):
            self.client.create_zaak_document(zaak_id="foo", doc_id="bar", body="bazz")

    def test_client_wraps_bad_structure_error(self, m):
        m.post(self.service.url, content=load_mock("dummy.xml"))

        with self.assertRaisesRegex(RegistrationFailed, r"^cannot find "):
            self.client.create_zaak_identificatie()

        with self.assertRaisesRegex(RegistrationFailed, r"^cannot find "):
            self.client.create_document_identificatie()


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

        self.form = FormFactory.create()
        self.fd = FormDefinitionFactory.create()
        self.fs = FormStepFactory.create(form=self.form, form_definition=self.fd)

    def test_plugin(self, m):
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
            additional_matcher=match_text("voegZaakdocumentToe_EdcLk01"),
        )

        form_options = dict()

        data = {
            "voornaam": "Foo",
        }
        submission = SubmissionFactory.create(form=self.form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )

        result = create_zaak_plugin(submission, form_options)
        self.assertEqual(
            result,
            {
                "zaak": "foo-zaak",
                "document": "bar-document",
            },
        )

        xml_doc = xml_from_request_history(m, 0)
        self.assertSoapXMLCommon(xml_doc)

        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)

        xml_doc = xml_from_request_history(m, 2)
        self.assertSoapXMLCommon(xml_doc)

        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
