import dataclasses
from decimal import Decimal
from unittest.mock import patch

from django.template import loader
from django.test import TestCase

import requests_mock
from freezegun import freeze_time
from lxml import etree
from lxml.etree import ElementTree
from privates.test import temp_private_root

from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from stuf.stuf_zds.client import nsmap
from stuf.stuf_zds.models import StufZDSConfig
from stuf.tests.factories import StufServiceFactory

from ....constants import RegistrationAttribute
from ....service import extract_submission_reference
from ..plugin import PartialDate, StufZDSRegistration


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


@freeze_time("2020-12-22")
@temp_private_root()
@requests_mock.Mocker()
class StufZDSPluginTests(StufTestBase):
    """
    test the plugin function
    """

    def setUp(self):
        self.service = StufServiceFactory.create()
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
                    "key": "coordinaat",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
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
                "coordinaat": [52.36673378967122, 4.893164274470299],
                "extra": "BuzzBazz",
            },
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo-zaak",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        m.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml",
                {"document_identificatie": "bar-document"},
            ),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        mock_task.id = 1

        form_options = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "123",
            "zds_zaaktype_status_omschrijving": "aaabbc",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        plugin = StufZDSRegistration("stuf")
        result = plugin.register_submission(submission, form_options)
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
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo-zaak",
                "//zkn:object/zkn:omschrijving": "my-form",
                "//zkn:object/zkn:betalingsIndicatie": "N.v.t.",
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:code": "zt-code",
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "111222333",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Foo",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Bar",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "de",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20001231",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum/@stuf:indOnvolledigeDatum": "V",
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "52.36673378967122 4.893164274470299",
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

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            6,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            6,
        )

    @patch("celery.app.task.Task.request")
    def test_plugin_payment(self, m, mock_task):
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
            ],
            form__name="my-form",
            form__product__price=Decimal("11.35"),
            form__payment_backend="demo",
            bsn="111222333",
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
        )
        self.assertTrue(submission.payment_required)

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo-zaak",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        m.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml",
                {"document_identificatie": "bar-document"},
            ),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        mock_task.id = 1

        form_options = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "123",
            "zds_zaaktype_status_omschrijving": "aaabbc",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        plugin = StufZDSRegistration("stuf")
        result = plugin.register_submission(submission, form_options)
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
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo-zaak",
                "//zkn:object/zkn:omschrijving": "my-form",
                "//zkn:object/zkn:betalingsIndicatie": "(Nog) niet",
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:code": "zt-code",
                "//zkn:object/zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "111222333",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Foo",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Bar",
            },
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

        # registration system would save the result
        submission.registration_result = {"zaak": "foo-zaak"}
        submission.save()

        # process the payment
        plugin.update_payment_status(submission, form_options)

        xml_doc = xml_from_request_history(m, 4)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo-zaak",
                "//zkn:object/zkn:betalingsIndicatie": "Geheel",
                "//zkn:object/zkn:laatsteBetaaldatum": "20201222",
            },
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_request.txt"
            ).count(),
            5,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            5,
        )

    @patch("celery.app.task.Task.request")
    def test_retried_registration_with_internal_reference(self, m, mock_task):
        """
        Assert that the internal reference is included in the "kenmerken".
        """
        submission = SubmissionFactory.from_components(
            completed=True,
            registration_in_progress=True,
            needs_on_completion_retry=True,
            public_registration_reference="OF-1234",
            components_list=[{"key": "dummy"}],
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo-zaak",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        m.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml",
                {"document_identificatie": "bar-document"},
            ),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock("voegZaakdocumentToe.xml"),
            additional_matcher=match_text("edcLk01"),
        )
        mock_task.id = 1

        form_options = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "123",
            "zds_zaaktype_status_omschrijving": "aaabbc",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        plugin = StufZDSRegistration("stuf")
        result = plugin.register_submission(submission, form_options)
        self.assertEqual(
            result,
            {
                "zaak": "foo-zaak",
                "document": "bar-document",
            },
        )

        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:kenmerk/zkn:kenmerk": "OF-1234",
                "//zkn:object/zkn:kenmerk/zkn:bron": "Open Formulieren",
            },
        )

    def test_reference_can_be_extracted(self, m):
        submission = SubmissionFactory.create(
            form__registration_backend="stuf-zds-create-zaak",
            completed=True,
            registration_success=True,
            registration_result={"zaak": "abcd1234"},
        )

        reference = extract_submission_reference(submission)

        self.assertEqual("abcd1234", reference)
