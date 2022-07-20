import dataclasses
from decimal import Decimal
from unittest.mock import patch

from django.test import tag

import requests_mock
from freezegun import freeze_time
from privates.test import temp_private_root

from openforms.logging.models import TimelineLogProxy
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.submissions.tests.mixins import VariablesTestMixin
from stuf.stuf_zds.models import StufZDSConfig
from stuf.stuf_zds.tests import StUFZDSTestBase
from stuf.stuf_zds.tests.utils import load_mock, match_text, xml_from_request_history
from stuf.tests.factories import StufServiceFactory

from ....constants import RegistrationAttribute
from ....exceptions import RegistrationFailed
from ....service import extract_submission_reference
from ....tasks import register_submission
from ..plugin import PartialDate, StufZDSRegistration


class StufZDSHelperTests(StUFZDSTestBase):
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
class StufZDSPluginTests(VariablesTestMixin, StUFZDSTestBase):
    """
    test the plugin function
    """

    def setUp(self):
        super().setUp()

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
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "type": "date",
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
            # we are deliberately NOT including this to simulate upgrades from earlier
            # versions where this configuration parameter was not available yet and is
            # thus missing from the JSON data
            # "zds_zaakdoc_vertrouwelijkheid": "OPENBAAR",
        }

        plugin = StufZDSRegistration("stuf")
        serializer = plugin.configuration_options(data=form_options)
        self.assertTrue(serializer.is_valid())

        result = plugin.register_submission(submission, serializer.validated_data)
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
                "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "123",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "aaabbc",
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
                "//zkn:object/zkn:vertrouwelijkAanduiding": "VERTROUWELIJK",
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

        # even on success, the intermediate results must be recorded:
        submission.refresh_from_db()
        self.assertEqual(
            submission.registration_result["intermediate"],
            {
                "zaaknummer": "foo-zaak",
                "zaak_created": True,
                "document_nummers": {
                    "pdf-report": "bar-document",
                    str(attachment.id): "bar-document",
                },
                "documents_created": {
                    "pdf-report": True,
                    str(attachment.id): True,
                },
            },
        )

    @patch("celery.app.task.Task.request")
    def test_plugin_payment(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
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
        serializer = plugin.configuration_options(data=form_options)
        self.assertTrue(serializer.is_valid())

        result = plugin.register_submission(submission, serializer.validated_data)
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
                "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "123",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "aaabbc",
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
        plugin.update_payment_status(submission, serializer.validated_data)

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
        serializer = plugin.configuration_options(data=form_options)
        self.assertTrue(serializer.is_valid())

        result = plugin.register_submission(submission, serializer.validated_data)
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

    @patch("celery.app.task.Task.request")
    def test_plugin_optional_fields(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "type": "date",
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
        SubmissionFileAttachmentFactory.create(
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
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        plugin = StufZDSRegistration("stuf")
        serializer = plugin.configuration_options(data=form_options)
        self.assertTrue(serializer.is_valid())

        result = plugin.register_submission(submission, serializer.validated_data)
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
        self.assertXPathNotExists(
            xml_doc, "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving"
        )
        self.assertXPathNotExists(xml_doc, "//zkn:heeft")

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
    def test_plugin_optional_fields_missing_status_description(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "type": "date",
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
        SubmissionFileAttachmentFactory.create(
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
            "zds_zaaktype_status_code": "zt-code",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        plugin = StufZDSRegistration("stuf")
        serializer = plugin.configuration_options(data=form_options)
        self.assertTrue(serializer.is_valid())

        result = plugin.register_submission(submission, serializer.validated_data)
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
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "111222333",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Foo",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Bar",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "de",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20001231",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum/@stuf:indOnvolledigeDatum": "V",
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "52.36673378967122 4.893164274470299",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "zt-code",
            },
        )
        self.assertXPathNotExists(
            xml_doc, "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving"
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
    def test_plugin_optional_fields_missing_status_code(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "tussenvoegsel",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                    },
                },
                {
                    "key": "geboortedatum",
                    "type": "date",
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
        SubmissionFileAttachmentFactory.create(
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
            "zds_zaaktype_status_omschrijving": "zt-status-omschrijving",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        plugin = StufZDSRegistration("stuf")
        serializer = plugin.configuration_options(data=form_options)
        self.assertTrue(serializer.is_valid())

        result = plugin.register_submission(submission, serializer.validated_data)
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
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "111222333",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Foo",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Bar",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "de",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20001231",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum/@stuf:indOnvolledigeDatum": "V",
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "52.36673378967122 4.893164274470299",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "zt-status-omschrijving",
            },
        )
        self.assertXPathNotExists(xml_doc, "//zkn:heeft/zkn:gerelateerde/zkn:code")

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

    def test_reference_can_be_extracted(self, m):
        submission = SubmissionFactory.create(
            form__registration_backend="stuf-zds-create-zaak",
            completed=True,
            registration_success=True,
            registration_result={"zaak": "abcd1234"},
        )

        reference = extract_submission_reference(submission)

        self.assertEqual("abcd1234", reference)


@tag("gh-1183")
@freeze_time("2020-12-22")
@temp_private_root()
class PartialRegistrationFailureTests(VariablesTestMixin, StUFZDSTestBase):
    """
    Test that partial results are stored and don't cause excessive registration calls.

    Issue #1183 -- case numbers are reserved to often, as a retry reserves a new one. It
    also happens that when certain other calls fail, a new Zaak is created which
    should not have been created again.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = StufServiceFactory.create()
        config = StufZDSConfig.get_solo()
        config.service = cls.service
        config.save()

        # set up a simple form to track the partial result storing state
        cls.submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                },
                {
                    "key": "achternaam",
                    "type": "textfield",
                },
            ],
            form__name="my-form",
            form__registration_backend="stuf-zds-create-zaak",
            form__registration_backend_options={
                "zds_zaaktype_code": "zt-code",
                "zds_zaaktype_status_code": "123",
                "zds_documenttype_omschrijving_inzending": "aaabbc",
            },
            completed=True,
            bsn="111222333",
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
        )

    def setUp(self):
        super().setUp()

        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)
        self.addCleanup(self.submission.refresh_from_db)

    def test_zaak_creation_fails_number_is_reserved(self):
        self.requests_mock.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo-zaak",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        self.requests_mock.post(
            self.service.soap_service.url,
            status_code=400,
            content=load_mock("soap-error.xml"),
            additional_matcher=match_text("zakLk01"),
        )

        with self.subTest("Initial registration fails"):
            register_submission(self.submission.id)

            self.submission.refresh_from_db()
            self.assertEqual(
                self.submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = self.submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results,
                {"zaaknummer": "foo-zaak"},
            )
            self.assertIn("traceback", self.submission.registration_result)

        with self.subTest("Retry does not create new zaaknummer"):
            with self.assertRaises(RegistrationFailed):
                register_submission(self.submission.id)

            self.submission.refresh_from_db()
            intermediate_results = self.submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results,
                {"zaaknummer": "foo-zaak"},
            )
            self.assertIn("traceback", self.submission.registration_result)
            num_requests_done = len(self.requests_mock.request_history)
            self.assertEqual(
                num_requests_done, 3
            )  # 1 create identificatie, 2 attempts to create zaak

            xml_doc = xml_from_request_history(self.requests_mock, 0)
            self.assertXPathEqualDict(
                xml_doc,
                {"//zkn:stuurgegevens/stuf:functie": "genereerZaakidentificatie"},
            )

            xml_doc = xml_from_request_history(self.requests_mock, 1)
            self.assertXPathEqualDict(
                xml_doc,
                {
                    "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                    "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                },
            )

            xml_doc = xml_from_request_history(self.requests_mock, 2)
            self.assertXPathEqualDict(
                xml_doc,
                {
                    "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                    "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                },
            )

    def test_doc_id_creation_fails_zaak_registration_succeeds(self):
        self.requests_mock.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo-zaak",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        self.requests_mock.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )
        self.requests_mock.post(
            self.service.soap_service.url,
            status_code=400,
            content=load_mock("soap-error.xml"),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )

        with self.subTest("Document id generation fails"):
            register_submission(self.submission.id)

            self.submission.refresh_from_db()
            self.assertEqual(
                self.submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = self.submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results,
                {
                    "zaaknummer": "foo-zaak",
                    "zaak_created": True,
                },
            )
            self.assertIn("traceback", self.submission.registration_result)

        with self.subTest("Retry does not create new zaak"):
            with self.assertRaises(RegistrationFailed):
                register_submission(self.submission.id)

            self.submission.refresh_from_db()
            intermediate_results = self.submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results,
                {
                    "zaaknummer": "foo-zaak",
                    "zaak_created": True,
                },
            )
            self.assertIn("traceback", self.submission.registration_result)
            num_requests_done = len(self.requests_mock.request_history)
            # 1. create zaak identificatie
            # 2. create zaak
            # 3. create document identificatie
            # 4. create document identificatie
            self.assertEqual(num_requests_done, 4)

            xml_doc = xml_from_request_history(self.requests_mock, 0)
            self.assertXPathEqualDict(
                xml_doc,
                {"//zkn:stuurgegevens/stuf:functie": "genereerZaakidentificatie"},
            )

            xml_doc = xml_from_request_history(self.requests_mock, 1)
            self.assertXPathEqualDict(
                xml_doc,
                {
                    "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                    "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                },
            )

            xml_doc = xml_from_request_history(self.requests_mock, 2)
            self.assertXPathEqualDict(
                xml_doc,
                {"//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie"},
            )

            xml_doc = xml_from_request_history(self.requests_mock, 3)
            self.assertXPathEqualDict(
                xml_doc,
                {"//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie"},
            )

    def test_doc_creation_failure_does_not_create_more_doc_ids(self):
        self.requests_mock.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "foo-zaak",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )
        self.requests_mock.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )
        self.requests_mock.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml",
                {"document_identificatie": "bar-document"},
            ),
            additional_matcher=match_text("genereerDocumentIdentificatie_Di02"),
        )
        self.requests_mock.post(
            self.service.soap_service.url,
            status_code=400,
            content=load_mock("soap-error.xml"),
            additional_matcher=match_text("edcLk01"),
        )

        with self.subTest("Document id generation fails"):
            register_submission(self.submission.id)

            self.submission.refresh_from_db()
            self.assertEqual(
                self.submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = self.submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results,
                {
                    "zaaknummer": "foo-zaak",
                    "zaak_created": True,
                    "document_nummers": {
                        "pdf-report": "bar-document",
                    },
                },
            )
            self.assertIn("traceback", self.submission.registration_result)

        with self.subTest("Retry does not create new zaak"):
            with self.assertRaises(RegistrationFailed):
                register_submission(self.submission.id)

            self.submission.refresh_from_db()
            intermediate_results = self.submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results,
                {
                    "zaaknummer": "foo-zaak",
                    "zaak_created": True,
                    "document_nummers": {
                        "pdf-report": "bar-document",
                    },
                },
            )
            self.assertIn("traceback", self.submission.registration_result)
            num_requests_done = len(self.requests_mock.request_history)
            # 1. create zaak identificatie
            # 2. create zaak
            # 3. create document identificatie (pdf)
            # 4. voegZaakDocumentToe (fails)
            # 5. voegZaakDocumentToe (fails again)
            self.assertEqual(num_requests_done, 5)

            xml_doc = xml_from_request_history(self.requests_mock, 2)
            self.assertXPathEqualDict(
                xml_doc,
                {"//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie"},
            )

            xml_doc = xml_from_request_history(self.requests_mock, 3)
            self.assertXPathEqualDict(
                xml_doc,
                {
                    "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                    "//zkn:stuurgegevens/stuf:entiteittype": "EDC",
                },
            )

            xml_doc = xml_from_request_history(self.requests_mock, 4)
            self.assertXPathEqualDict(
                xml_doc,
                {
                    "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                    "//zkn:stuurgegevens/stuf:entiteittype": "EDC",
                },
            )
