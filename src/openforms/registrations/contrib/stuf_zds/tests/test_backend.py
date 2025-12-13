import dataclasses
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from django.test import override_settings, tag

import requests_mock
from freezegun import freeze_time
from lxml import etree
from privates.test import temp_private_root
from requests import ConnectTimeout
from zgw_consumers.test.factories import ServiceFactory

from openforms.authentication.service import AuthAttribute
from openforms.authentication.tests.factories import RegistratorInfoFactory
from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.forms.tests.factories import (
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.logging.models import TimelineLogProxy
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.prefill.service import prefill_variables
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tasks import on_post_submission_event, pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin
from stuf.stuf_zds.client import PaymentStatus as StuFPaymentStatus
from stuf.stuf_zds.models import StufZDSConfig
from stuf.stuf_zds.tests import StUFZDSTestBase
from stuf.stuf_zds.tests.utils import load_mock, match_text, xml_from_request_history
from stuf.tests.factories import StufServiceFactory

from ....constants import RegistrationAttribute
from ....exceptions import RegistrationFailed
from ..options import default_payment_status_update_mapping
from ..plugin import PLUGIN_IDENTIFIER, PartialDate, StufZDSRegistration
from ..typing import RegistrationOptions

TESTS_DIR = Path(__file__).parent.resolve()


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

        # date objects
        actual = PartialDate.parse(date(2000, 1, 2))
        self.assertEqual(dict(year=2000, month=1, day=2), dataclasses.asdict(actual))
        self.assertEqual("20000102", actual.value)
        self.assertEqual("V", actual.indicator)

        actual = PartialDate.parse(datetime(2000, 1, 2, 12, 34, 56))
        self.assertEqual(dict(year=2000, month=1, day=2), dataclasses.asdict(actual))
        self.assertEqual("20000102", actual.value)
        self.assertEqual("V", actual.indicator)

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
class StufZDSPluginTests(StUFZDSTestBase):
    """
    test the plugin function
    """

    def setUp(self):
        super().setUp()

        self.service = StufServiceFactory.create()
        config = StufZDSConfig.get_solo()
        config.service = self.service
        config.save()
        self.addCleanup(StufZDSConfig.clear_cache)

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
                {
                    "key": "language_code",
                },
                {"key": "cosignerEmail", "type": "cosign"},
            ],
            form__name="my-form",
            bsn="111222333",
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "extra": "BuzzBazz",
                "language_code": "Dothraki",  # some form widget defined by form designer
            },
            language_code="en",
            cosigned=True,
            co_sign_data__value="123456782",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
                "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "123",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "aaabbc",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "123456782",
            },
        )
        # extraElementen
        self.assertXPathEqual(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='extra']",
            "BuzzBazz",
        )

        # first language_code contains the submission language
        self.assertXPathEqual(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='language_code' and position()=1]",
            "en",
        )
        self.assertXPathEqual(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='language_code' and not(position()=1)]",
            "Dothraki",
        )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )
        xml_doc = xml_from_request_history(m, 2)
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
        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 4)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "my-attachment.doc",
                "//zkn:object/zkn:inhoud/@xmime:contentType": "application/msword",
                "//zkn:object/zkn:formaat": "application/msword",
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
    def test_plugin_natuurlijk_persoon_initiator(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voorletters",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voorletters,
                    },
                },
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
                    "key": "geslachtsaanduiding",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsaanduiding,
                    },
                },
                {
                    "key": "postcode",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_postcode,
                    },
                },
                {
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
                {
                    "key": "contactpersoonNaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_contactpersoonNaam,
                    },
                },
                {
                    "key": "telefoonnummer",
                    "type": "phoneNumber",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_telefoonnummer,
                    },
                },
                {
                    "key": "emailadres",
                    "type": "email",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_emailadres,
                    },
                },
            ],
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "postcode": "1000 aa",
                "geboortedatum": "2000-12-31",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "voorletters": "J.W.",
                "geslachtsaanduiding": "mannelijk",
                "contactpersoonNaam": "Naam",
                "telefoonnummer": "0612345678",
                "emailadres": "foo@example.com",
            },
            bsn="111222333",
            form__name="my-form",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "J.W.",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsaanduiding": "M",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:heeftAlsAanspreekpunt/zkn:gerelateerde/zkn:naam": "Naam",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:heeftAlsAanspreekpunt/zkn:gerelateerde/zkn:telefoonnummer": "0612345678",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:heeftAlsAanspreekpunt/zkn:gerelateerde/zkn:emailadres": "foo@example.com",
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
                "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "123",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "aaabbc",
            },
        )

        # postcode should also be converted (through template filters) to uppercase (#2977)
        with self.subTest("#2422: postcode must be normalized"):
            self.assertXPathEqual(
                xml_doc,
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:verblijfsadres/bg:aoa.postcode",
                "1000AA",
            )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 2)
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
        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 4)
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
            5,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            5,
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
    def test_plugin_natuurlijk_persoon_without_auth(self, m, mock_task):
        """Assert that the values of Zaak fields coupled to StUF-ZDS/ZGW are sent to the
        backend even if the client (a natural person) is not authenticated"""

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voorletters",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voorletters,
                    },
                },
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
                    "key": "geslachtsaanduiding",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsaanduiding,
                    },
                },
                {
                    "key": "postcode",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_postcode,
                    },
                },
                {
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "postcode": "1000 AA",
                "geboortedatum": "2000-12-31",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "voorletters": "J.W.",
                "geslachtsaanduiding": "mannelijk",
            },
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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

        form_options = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        self.assertFalse(submission.is_authenticated)

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
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo-zaak",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "N",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Foo",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Bar",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "de",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20001231",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "J.W.",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsaanduiding": "M",
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
            },
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
    def test_plugin_nietNatuurlijkPersoon_without_auth(self, m, mock_task):
        """Assert that the values of Zaak fields coupled to StUF-ZDS/ZGW are sent to the
        backend even if the client (a company) is not authenticated"""

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_handelsnaam,
                    },
                },
                {
                    "key": "postcode",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_postcode,
                    },
                },
            ],
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "handelsnaam": "Foo",
                "postcode": "2022XY",
            },
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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

        form_options = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        self.assertFalse(submission.is_authenticated)

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
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo-zaak",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:nietNatuurlijkPersoon/bg:statutaireNaam": "Foo",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:nietNatuurlijkPersoon/bg:authentiek": "N",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:nietNatuurlijkPersoon/bg:bezoekadres/bg:aoa.postcode": "2022XY",
            },
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
    def test_plugin_vestiging_initiator(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_handelsnaam,
                    },
                },
                {
                    "key": "postcode",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_postcode,
                    },
                },
                {
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
                {
                    "key": "vestigingsNummer",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_vestigingsnummer,
                    },
                },
            ],
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "vestigingsNummer": "87654321",
            },
            kvk="12345678",
            form__name="my-form",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
                "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "123",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "aaabbc",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:vestiging/bg:vestigingsNummer": "87654321",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:vestiging/bg:handelsnaam": "ACME",
            },
        )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 2)
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
        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 4)
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
            5,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            5,
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
    def test_plugin_vestiging_initiator_kvk_only(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_handelsnaam,
                    },
                },
                {
                    "key": "postcode",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_postcode,
                    },
                },
                {
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            kvk="12345678",
            form__name="my-form",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
                "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "123",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "aaabbc",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:nietNatuurlijkPersoon/bg:inn.nnpId": "12345678",
            },
        )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 2)
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
        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 4)
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
            5,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            5,
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
    def test_plugin_vestiging_initiator_kvk_and_vestigingsnummer(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "handelsnaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_handelsnaam,
                    },
                },
                {
                    "key": "postcode",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_postcode,
                    },
                },
                {
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
                {
                    "key": "vestigingsNummer",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_vestigingsnummer,
                    },
                },
            ],
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "vestigingsNummer": "87654321",
            },
            kvk="12345678",
            form__name="my-form",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
                "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "123",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "aaabbc",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:vestiging/bg:handelsnaam": "ACME",
            },
        )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 2)
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
        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 4)
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
            5,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            5,
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
    def test_plugin_medewerker(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voorletters",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voorletters,
                    },
                },
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
                    "key": "geslachtsaanduiding",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_geslachtsaanduiding,
                    },
                },
                {
                    "key": "postcode",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_postcode,
                    },
                },
                {
                    "key": "coordinaat",
                    "type": "map",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "postcode": "1000 AA",
                "geboortedatum": "2000-12-31",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
                "voorletters": "J.W.",
                "geslachtsaanduiding": "mannelijk",
            },
            bsn="111222333",
            form__name="my-form",
            form__product__price=Decimal("0"),
            form__payment_backend="demo",
        )
        RegistratorInfoFactory.create(submission=submission, value="123456782")
        config = StufZDSConfig.get_solo()
        config.zaakbetrokkene_registrator_omschrijving = "registrator"
        config.save()

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
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "J.W.",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsaanduiding": "M",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene/zkn:gerelateerde/zkn:medewerker/zkn:identificatie": "123456782",  # Identificatie of the employee
                "//zkn:object/zkn:heeftAlsOverigBetrokkene/zkn:omschrijving": "registrator",
                "//zkn:object/zkn:anderZaakObject/zkn:omschrijving": "coordinaat",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
                "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving": "zt-omschrijving",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "123",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "aaabbc",
            },
        )

    @patch("celery.app.task.Task.request")
    def test_plugin_medewerker_without_auth(self, m, mock_task):
        """Assert that the values of Zaak fields coupled to StUF-ZDS/ZGW are sent to the
        backend if the Zaak is initiated by a non-authenticated employee"""

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "medewerker_nummer",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_medewerker_nummer,
                    },
                },
                {
                    "key": "voornamen",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
            ],
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "medewerker_nummer": "007",
            },
        )

        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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

        form_options = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }

        self.assertFalse(submission.is_authenticated)

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
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Lk01",
                "//zkn:stuurgegevens/stuf:entiteittype": "ZAK",
                "//zkn:object/zkn:identificatie": "foo-zaak",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:medewerker/zkn:identificatie": "007",
            },
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
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
        )
        self.assertTrue(submission.payment_required)

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
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 2)
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

        xml_doc = xml_from_request_history(m, 3)
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
            4,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            4,
        )

    @patch("celery.app.task.Task.request")
    def test_retried_registration_with_internal_reference(self, m, mock_task):
        """
        Assert that the internal reference is included in the "kenmerken".
        """
        submission = SubmissionFactory.from_components(
            registration_in_progress=True,
            needs_on_completion_retry=True,
            public_registration_reference="foo-zaak",
            pre_registration_completed=False,
            registration_result={"temporary_internal_reference": "OF-1234"},
            components_list=[{"key": "dummy"}],
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
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
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
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
            },
        )
        self.assertXPathNotExists(
            xml_doc, "//zkn:isVan/zkn:gerelateerde/zkn:omschrijving"
        )
        self.assertXPathNotExists(xml_doc, "//zkn:heeft")

        # extraElementen
        self.assertXPathEqual(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='extra']",
            "BuzzBazz",
        )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 2)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "open-forms-inzending.pdf",
                "//zkn:object/zkn:formaat": "application/pdf",
            },
        )

        # attachment
        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 4)
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
            5,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            5,
        )

    @patch("celery.app.task.Task.request")
    def test_plugin_map_with_pointer(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "coordinaat",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            form__name="my-form",
            bsn="111222333",
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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
        self.assertXPathEqual(
            xml_doc,
            "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos",
            "4.893164274470299 52.36673378967122",
        )

    @patch("celery.app.task.Task.request")
    def test_plugin_map_with_polygon(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "coordinaat",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            form__name="my-form",
            bsn="111222333",
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "coordinaat": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [5.275725, 52.134743],
                            [5.256707, 52.123972],
                            [5.286552, 52.123035],
                            [5.275725, 52.134743],
                        ]
                    ],
                },
            },
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Polygon/gml:exterior/gml:LinearRing/gml:pos[1]": "5.275725 52.134743",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Polygon/gml:exterior/gml:LinearRing/gml:pos[2]": "5.256707 52.123972",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Polygon/gml:exterior/gml:LinearRing/gml:pos[3]": "5.286552 52.123035",
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Polygon/gml:exterior/gml:LinearRing/gml:pos[4]": "5.275725 52.134743",
            },
        )

    @patch("celery.app.task.Task.request")
    def test_plugin_map_with_line_string(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "coordinaat",
                    "registration": {
                        "attribute": RegistrationAttribute.locatie_coordinaat,
                    },
                },
            ],
            form__name="my-form",
            bsn="111222333",
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "coordinaat": {
                    "type": "LineString",
                    "coordinates": [
                        [5.313637, 52.128128],
                        [5.28987, 52.132218],
                        [5.273187, 52.1287],
                    ],
                },
            },
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="my-attachment.doc",
            content_type="application/msword",
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
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:LineString/gml:posList": "5.313637 52.128128 5.28987 52.132218 5.273187 52.1287",
            },
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
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
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
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
                "//zkn:heeft/zkn:gerelateerde/zkn:code": "zt-code",
            },
        )
        self.assertXPathNotExists(
            xml_doc, "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving"
        )

        # extraElementen
        self.assertXPathEqual(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='extra']",
            "BuzzBazz",
        )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 2)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "open-forms-inzending.pdf",
                "//zkn:object/zkn:formaat": "application/pdf",
            },
        )

        # attachment
        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 4)
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
            5,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            5,
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
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
                "geboortedatum": "2000-12-31",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
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
                "//zkn:object/zkn:anderZaakObject/zkn:lokatie/gml:Point/gml:pos": "4.893164274470299 52.36673378967122",
                "//zkn:heeft/zkn:gerelateerde/zkn:omschrijving": "zt-status-omschrijving",
            },
        )
        self.assertXPathNotExists(xml_doc, "//zkn:heeft/zkn:gerelateerde/zkn:code")

        # extraElementen
        self.assertXPathEqual(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='extra']",
            "BuzzBazz",
        )

        # don't expect registered data in extraElementen
        self.assertXPathNotExists(
            xml_doc, "//stuf:extraElementen/stuf:extraElement[@naam='voornaam']"
        )

        # PDF report
        xml_doc = xml_from_request_history(m, 1)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 2)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:object/zkn:inhoud/@stuf:bestandsnaam": "open-forms-inzending.pdf",
                "//zkn:object/zkn:formaat": "application/pdf",
            },
        )

        # attachment
        xml_doc = xml_from_request_history(m, 3)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//zkn:stuurgegevens/stuf:berichtcode": "Di02",
                "//zkn:stuurgegevens/stuf:functie": "genereerDocumentidentificatie",
            },
        )

        xml_doc = xml_from_request_history(m, 4)
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
            5,
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/stuf_zds_success_response.txt"
            ).count(),
            5,
        )

    def test_pre_registration_goes_wrong_sets_internal_reference(self, m):
        submission = SubmissionFactory.from_components(
            [],
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            form__registration_backend="stuf-zds-create-zaak",
            form__registration_backend_options={
                "zds_zaaktype_code": "zt-code",
                "zds_documenttype_omschrijving_inzending": "aaabbc",
            },
            kvk="12345678",
            completed_not_preregistered=True,
        )

        m.post(
            self.service.soap_service.url,
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
            exc=ConnectTimeout,
        )

        form_options = {
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "123",
            "zds_zaaktype_status_omschrijving": "aaabbc",
            "zds_documenttype_omschrijving_inzending": "aaabbc",
        }
        plugin = StufZDSRegistration("stuf")
        serializer = plugin.configuration_options(data=form_options)
        serializer.is_valid()

        with patch(
            "openforms.submissions.public_references.generate_unique_submission_reference",
            return_value="OF-TEST!",
        ):
            pre_registration(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "OF-TEST!")
        self.assertFalse(submission.pre_registration_completed)

    def test_retry_pre_registration_task(self, m):
        submission = SubmissionFactory.from_components(
            [],
            public_registration_reference="OF-TEMP",
            completed=True,
            pre_registration_completed=False,
            registration_result={"temporary_internal_reference": "OF-TEMP"},
            submitted_data={
                "handelsnaam": "ACME",
                "postcode": "1000 AA",
                "coordinaat": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            kvk="12345678",
            form__registration_backend="stuf-zds-create-zaak",
            form__registration_backend_options={
                "zds_zaaktype_code": "zt-code",
                "zds_zaaktype_omschrijving": "zt-omschrijving",
                "zds_zaaktype_status_code": "123",
                "zds_zaaktype_status_omschrijving": "aaabbc",
                "zds_documenttype_omschrijving_inzending": "aaabbc",
            },
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "ZAAK-FOOO",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )

        pre_registration(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "ZAAK-FOOO")
        self.assertIn("temporary_internal_reference", submission.registration_result)
        self.assertEqual(
            submission.registration_result["temporary_internal_reference"], "OF-TEMP"
        )

    def test_backend_preregistration_sets_reference(self, m):
        m.post(
            self.service.soap_service.url,
            content=load_mock(
                "genereerZaakIdentificatie.xml",
                {
                    "zaak_identificatie": "ZAAK-FOOO",
                },
            ),
            additional_matcher=match_text("genereerZaakIdentificatie_Di02"),
        )

        submission = SubmissionFactory.create(
            form__registration_backend="stuf-zds-create-zaak",
            form__registration_backend_options={
                "zds_zaaktype_code": "zt-code",
                "zds_documenttype_omschrijving_inzending": "aaabbc",
            },
            completed_not_preregistered=True,
        )

        self.assertEqual(submission.public_registration_reference, "")

        pre_registration(submission.id, PostSubmissionEvents.on_completion)
        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "ZAAK-FOOO")

    @patch("celery.app.task.Task.request")
    def test_user_defined_variables(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
            ],
            form__name="my-form",
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "voornaam": "Foo",
            },
            language_code="en",
            completed=True,
        )

        SubmissionValueVariableFactory.create(
            key="userDefinedVarString",
            submission=submission,
            form_variable__user_defined=True,
            value="value",
        )
        SubmissionValueVariableFactory.create(
            key="userDefinedVarJson",
            submission=submission,
            form_variable__user_defined=True,
            value={"key1": "value1", "key2": ["value2"]},
        )
        SubmissionValueVariableFactory.create(
            key="userDefinedVarArray",
            submission=submission,
            form_variable__user_defined=True,
            value=["value1", {"key1": "value2"}],
        )

        m.post(
            self.service.soap_service.url,
            content=load_mock("creeerZaak.xml"),
            additional_matcher=match_text("zakLk01"),
        )
        # Needed for the PDF report
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

        plugin.register_submission(submission, serializer.validated_data)

        xml_request_body = xml_from_request_history(m, 0)

        self.assertXPathEqual(
            xml_request_body,
            "//stuf:extraElementen/stuf:extraElement[@naam='userDefinedVarString']",
            "value",
        )
        self.assertXPathEqual(
            xml_request_body,
            "//stuf:extraElementen/stuf:extraElement[@naam='userDefinedVarArray.0']",
            "value1",
        )
        self.assertXPathEqual(
            xml_request_body,
            "//stuf:extraElementen/stuf:extraElement[@naam='userDefinedVarArray.1.key1']",
            "value2",
        )
        self.assertXPathEqual(
            xml_request_body,
            "//stuf:extraElementen/stuf:extraElement[@naam='userDefinedVarJson.key1']",
            "value1",
        )
        self.assertXPathEqual(
            xml_request_body,
            "//stuf:extraElementen/stuf:extraElement[@naam='userDefinedVarJson.key2.0']",
            "value2",
        )

    @patch("celery.app.task.Task.request")
    def test_plugin_with_extra_unmapped_number_data(self, m, mock_task):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "extra_number",
                },
            ],
            form__name="my-form",
            bsn="111222333",
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={"extra_number": 2023},
            language_code="en",
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

        # extraElementen
        self.assertXPathEqual(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='extra_number']",
            "2023",
        )


class StufZDSPluginVCRTests(OFVCRMixin, StUFZDSTestBase):
    VCR_TEST_FILES = TESTS_DIR / "files"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost/stuf-zds"
        )
        config = StufZDSConfig.get_solo()
        config.service = cls.zds_service
        config.save()
        cls.addClassCleanup(StufZDSConfig.clear_cache)

        cls.options: RegistrationOptions = {
            "zds_zaaktype_code": "foo",
            "zds_documenttype_omschrijving_inzending": "foo",
            "zds_zaakdoc_vertrouwelijkheid": "GEHEIM",
        }

    @tag("gh-5754")
    def test_date_related_values_in_extra_elementen(self):
        """Ensure that date-related values in extraElementen are formatted correctly."""
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "date",
                    "type": "date",
                    "label": "Date",
                },
                {
                    "key": "datetime",
                    "type": "datetime",
                    "label": "Datetime",
                },
                {
                    "key": "time",
                    "type": "time",
                    "label": "time",
                },
            ],
            form__name="my-form",
            bsn="111222333",
            public_registration_reference="foo-zaak",
            registration_result={"intermediate": {"zaaknummer": "foo-zaak"}},
            submitted_data={
                "date": "2025-11-18",
                "time": "14:21:00",
                "datetime": "2025-11-18T14:21:00+01:00",
            },
            language_code="en",
        )

        plugin = StufZDSRegistration("stuf")
        plugin.register_submission(submission, self.options)

        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)
        self.assertSoapXMLCommon(xml_doc)

        # Ensure that date-related values are formatted correctly
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//stuf:extraElementen/stuf:extraElement[@naam='date']": "2025-11-18",
                "//stuf:extraElementen/stuf:extraElement[@naam='datetime']": "2025-11-18T14:21:00+01:00",
                "//stuf:extraElementen/stuf:extraElement[@naam='time']": "14:21:00",
            },
        )


@freeze_time("2020-12-22")
@temp_private_root()
@requests_mock.Mocker()
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class StufZDSPluginPaymentTests(StUFZDSTestBase):
    def setUp(self):
        super().setUp()

        self.service = StufServiceFactory.create()
        config = StufZDSConfig.get_solo()
        config.service = self.service
        config.save()
        self.addCleanup(StufZDSConfig.clear_cache)

    @tag("gh-4145")
    def test_payment_status_is_correct_on_payment_update(self, m):
        """
        #4145:
        Testing that if 'wait_for_payment_to_register' is True, when the payment is completed and the submission is
        registered, the right payment status is sent to the StUF-ZDS backend.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                },
            ],
            submitted_data={"email": "test@test.nl"},
            with_public_registration_reference=True,
            confirmation_email_sent=True,
            form__registration_backend="stuf-zds-create-zaak",
            form__registration_backend_options={
                "zds_zaaktype_code": "zt-code",
                "zds_documenttype_omschrijving_inzending": "aaabbc",
            },
            form__name="Pretty Form",
            with_completed_payment=True,
            registration_result={"intermediate": {"zaaknummer": "ZAAK-TRALALA"}},
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

        with patch(
            "openforms.registrations.tasks.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(wait_for_payment_to_register=True),
        ):
            on_post_submission_event(
                submission.id, PostSubmissionEvents.on_payment_complete
            )

        submission.refresh_from_db()

        self.assertTrue(
            submission.payments.filter(status=PaymentStatus.registered).exists()
        )

        xml_doc = xml_from_request_history(m, 0)

        self.assertXPathEqual(
            xml_doc,
            "//zkn:betalingsIndicatie",
            StuFPaymentStatus.FULL,
        )

    def test_payment_status_is_correct_if_not_waiting_for_payment(self, m):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                },
            ],
            submitted_data={"email": "test@test.nl"},
            with_public_registration_reference=True,
            form__registration_backend="stuf-zds-create-zaak",
            form__registration_backend_options={
                "zds_zaaktype_code": "zt-code",
                "zds_documenttype_omschrijving_inzending": "aaabbc",
            },
            form__name="Pretty Form",
            form__product__price=Decimal("10.00"),
            form__payment_backend="demo",
            registration_result={},
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

        with patch(
            "openforms.registrations.tasks.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(wait_for_payment_to_register=False),
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        xml_doc = xml_from_request_history(m, 0)

        self.assertXPathEqual(
            xml_doc,
            "//zkn:betalingsIndicatie",
            StuFPaymentStatus.NOT_YET,
        )

    def test_payment_status_is_correct_when_no_payment_required(self, m):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                },
            ],
            submitted_data={"email": "test@test.nl"},
            with_public_registration_reference=True,
            form__registration_backend="stuf-zds-create-zaak",
            form__registration_backend_options={
                "zds_zaaktype_code": "zt-code",
                "zds_documenttype_omschrijving_inzending": "aaabbc",
            },
            form__name="Pretty Form",
            registration_result={},
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

        on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        xml_doc = xml_from_request_history(m, 0)

        self.assertXPathEqual(
            xml_doc,
            "//zkn:betalingsIndicatie",
            StuFPaymentStatus.NVT,
        )


@temp_private_root()
class StufZDSPluginPaymentVCRTests(OFVCRMixin, StUFZDSTestBase):
    VCR_TEST_FILES = TESTS_DIR / "files"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost/stuf-zds"
        )
        config = StufZDSConfig.get_solo()
        config.service = cls.zds_service
        config.save()
        cls.addClassCleanup(StufZDSConfig.clear_cache)

        cls.options: RegistrationOptions = {
            "zds_zaaktype_code": "foo",
            "zds_documenttype_omschrijving_inzending": "foo",
            "zds_zaakdoc_vertrouwelijkheid": "GEHEIM",
            "payment_status_update_mapping": default_payment_status_update_mapping(),
        }
        cls.submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                    "label": "Voornaam",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
            ],
            form__name="my-form",
            bsn="111222333",
            submitted_data={"voornaam": "Foo"},
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        # can't pass this as part of `SubmissionFactory.from_components`
        cls.submission.price = Decimal("40.00")
        cls.submission.save()
        SubmissionPaymentFactory.create(
            submission=cls.submission,
            amount=Decimal("25.00"),
            public_order_id="foo",
            status=PaymentStatus.completed,
            provider_payment_id="123456",
        )
        SubmissionPaymentFactory.create(
            submission=cls.submission,
            amount=Decimal("15.00"),
            public_order_id="bar",
            status=PaymentStatus.registered,
            provider_payment_id="654321",
        )
        # failed payment, should be ignored
        SubmissionPaymentFactory.create(
            submission=cls.submission,
            amount=Decimal("15.00"),
            public_order_id="baz",
            status=PaymentStatus.failed,
            provider_payment_id="6789",
        )

    def test_set_zaak_payment(self):
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        plugin.update_payment_status(self.submission, self.options)

        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)
        self.assertSoapXMLCommon(xml_doc)
        expected_items = {
            "payment_completed": "true",
            "payment_amount": "40.0",
            "payment_public_order_ids.0": "foo",
            "payment_public_order_ids.1": "bar",
            "provider_payment_ids.0": "123456",
            "provider_payment_ids.1": "654321",
        }
        for name, value in expected_items.items():
            with self.subTest(extra_element=name, value=value):
                self.assertXPathEqual(
                    xml_doc,
                    f"//stuf:extraElementen/stuf:extraElement[@naam='{name}']",
                    value,
                )

    def test_set_zaak_payment_incorrect_payment_status_update_mapping(self):
        """
        Non-existent fields in the payment_status_update_mapping should be ignored
        """
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptions = {
            "zds_zaaktype_code": "foo",
            "zds_documenttype_omschrijving_inzending": "foo",
            "zds_zaakdoc_vertrouwelijkheid": "GEHEIM",
            "payment_status_update_mapping": [
                {"form_variable": "payment_amount", "stuf_name": "paymentAmount"},
                {"form_variable": "non-existent-field", "stuf_name": "foo"},
            ],
        }

        plugin.update_payment_status(self.submission, options)

        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)
        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqual(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='paymentAmount']",
            "40.0",
        )

    def test_register_submission_with_payment(self):
        """
        Assert that payment attributes are included when creating the zaak, in case
        the registration is deferred until the payment is received
        """
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        plugin.register_submission(self.submission, self.options)

        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)
        self.assertSoapXMLCommon(xml_doc)
        expected_items = {
            "payment_completed": "true",
            "payment_amount": "40.0",
            "payment_public_order_ids.0": "foo",
            "payment_public_order_ids.1": "bar",
            "provider_payment_ids.0": "123456",
            "provider_payment_ids.1": "654321",
        }
        for name, value in expected_items.items():
            with self.subTest(extra_element=name, value=value):
                self.assertXPathEqual(
                    xml_doc,
                    f"//stuf:extraElementen/stuf:extraElement[@naam='{name}']",
                    value,
                )


class StufZDSPluginPartnersComponentVCRTests(OFVCRMixin, StUFZDSTestBase):
    VCR_TEST_FILES = TESTS_DIR / "files"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)
        cls.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost/stuf-zds"
        )
        config = StufZDSConfig.get_solo()
        config.service = cls.zds_service
        config.zaakbetrokkene_partners_omschrijving = "A description"
        config.save()
        cls.addClassCleanup(StufZDSConfig.clear_cache)

        cls.options: RegistrationOptions = {
            "zds_zaaktype_code": "foo",
            "zds_documenttype_omschrijving_inzending": "foo",
            "zds_zaakdoc_vertrouwelijkheid": "GEHEIM",
        }

        hc_config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/"
            ),
            brp_personen_version=BRPVersions.v20,
        )
        hc_config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=hc_config,
        )

        global_config = GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        )
        global_config_patcher = patch(
            "openforms.config.models.GlobalConfiguration.get_solo",
            return_value=global_config,
        )

        hc_config = hc_config_patcher.start()
        global_config = global_config_patcher.start()
        cls.addClassCleanup(hc_config_patcher.stop)
        cls.addClassCleanup(global_config_patcher.stop)

    def test_create_zaak_with_partners_as_betrokkene(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partnersKey",
                    "type": "partners",
                    "label": "Partners",
                    "registration": {"attribute": RegistrationAttribute.partners},
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009921",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        FormVariableFactory.create(
            key="partners_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partnersKey",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission)
        self.plugin.register_submission(submission, self.options)

        stuf_request = self.cassette.requests[1]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)

        # make sure two partners are present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            2,
        )

        # assert all the expected properties are present
        self.assertXPathContainsDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "000009921",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # partners
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": [
                    "999995182",
                    "123456782",
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": [
                    "J"
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": [
                    "Anna Maria Petra",
                    "Test second partner",
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": [
                    "A.M.P.",
                    "T.s.p.",
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": [
                    "Jansma",
                    "Test",
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "19450418",
            },
        )

        # make sure that nothing is registered as extraElement
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.bsn']",
        )
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='partners_immutable.0.bsn']",
        )

    def test_create_zaak_with_partners_as_extraElementen(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partnersKey",
                    "type": "partners",
                    "label": "Partners",
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009921",
            language_code="en",
            public_registration_reference="abc890",
            registration_result={"zaak": "890"},
        )
        FormVariableFactory.create(
            key="partners_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partnersKey",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission)
        self.plugin.register_submission(submission, self.options)

        stuf_request = self.cassette.requests[1]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.bsn']": "999995182",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.firstNames']": "Anna Maria Petra",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.initials']": "A.M.P.",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.affixes']": "",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.lastName']": "Jansma",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.dateOfBirth']": "1945-04-18",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.bsn']": "123456782",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.firstNames']": "Test second partner",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.initials']": "T.s.p.",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.affixes']": "",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.lastName']": "Test",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.dateOfBirth']": "1945-04-18",
            },
        )

        # make sure that nothing is registered as zaakbetrokkene
        self.assertXPathNotExists(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
        )

    def test_create_zaak_with_no_partners_retrieved(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partnersKey",
                    "type": "partners",
                    "label": "Partners",
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009830",
            language_code="en",
            public_registration_reference="abc999",
            registration_result={"zaak": "9990"},
        )
        FormVariableFactory.create(
            key="partners_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partnersKey",
                "min_age": None,
                "max_age": None,
            },
        )
        prefill_variables(submission)

        self.plugin.register_submission(submission, self.options)

        stuf_request = self.cassette.requests[1]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathNotExists(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
        )
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.bsn']",
        )

    def test_create_zaak_with_hidden_partners(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partnersKey",
                    "type": "partners",
                    "label": "Partners",
                    "registration": {"attribute": RegistrationAttribute.partners},
                    "hidden": True,
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009830",
            language_code="en",
            public_registration_reference="abc999",
            registration_result={"zaak": "9990"},
        )
        FormVariableFactory.create(
            key="partners_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partnersKey",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission)
        self.plugin.register_submission(submission, self.options)

        stuf_request = self.cassette.requests[1]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathNotExists(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
        )
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.bsn']",
        )

    def test_only_relevant_variables_are_taken_into_account(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partnersKey",
                    "type": "partners",
                    "label": "Partners",
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009921",
            language_code="en",
            public_registration_reference="abc890",
            registration_result={"zaak": "890"},
        )
        FormVariableFactory.create(
            key="irrelevant_variable",
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "someKey",
                "min_age": None,
                "max_age": None,
            },
        )
        FormVariableFactory.create(
            key="partners_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partnersKey",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission)
        self.plugin.register_submission(submission, self.options)

        stuf_request = self.cassette.requests[1]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.bsn']": "999995182",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.firstNames']": "Anna Maria Petra",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.initials']": "A.M.P.",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.affixes']": "",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.lastName']": "Jansma",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.0.dateOfBirth']": "1945-04-18",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.bsn']": "123456782",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.firstNames']": "Test second partner",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.initials']": "T.s.p.",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.affixes']": "",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.lastName']": "Test",
                "//stuf:extraElementen/stuf:extraElement[@naam='partnersKey.1.dateOfBirth']": "1945-04-18",
            },
        )

    @tag("gh-5770")
    def test_partners_registration_with_date_of_birth_as_str(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            components_list=[
                {
                    "key": "stuf_bg_partners_mutable",
                    "type": "partners",
                    "label": "Partners",
                },
            ],
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
            submitted_data={
                "stuf_bg_partners_mutable": [
                    {
                        "bsn": "123123123",
                        "firstNames": "Belly",
                        "initials": "K",
                        "affixes": "van",
                        "lastName": "Doe",
                        # the date of birth is of type datetime.date when we submit the step
                        "dateOfBirth": date(1985, 6, 15),
                        "deceased": None,
                        "dateOfBirthPrecision": "date",
                    }
                ]
            },
            completed=True,
        )

        SubmissionValueVariableFactory.create(
            key="stuf_bg_partners_immutable",
            submission=submission,
            form_variable__user_defined=True,
            form_variable__prefill_plugin="family_members",
            form_variable__prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "stuf_bg_partners_mutable",
            },
            value=[
                {
                    "bsn": "123123123",
                    "firstNames": "Belly",
                    "initials": "K",
                    "affixes": "van",
                    "lastName": "Doe",
                    # date of birth as an str in order to have the regression test
                    "dateOfBirth": "19850615",
                    "deceased": None,
                }
            ],
        )

        try:
            self.plugin.register_submission(submission, self.options)
        except AttributeError as e:
            raise self.failureException("Registration failed unexpectedly") from e


class StufZDSPluginChildrenComponentVCRTests(OFVCRMixin, StUFZDSTestBase):
    VCR_TEST_FILES = TESTS_DIR / "files"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)
        cls.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost/stuf-zds"
        )
        config = StufZDSConfig.get_solo()
        config.service = cls.zds_service
        config.zaakbetrokkene_children_omschrijving = "A description"
        config.save()
        cls.addClassCleanup(StufZDSConfig.clear_cache)

        cls.options: RegistrationOptions = {
            "zds_zaaktype_code": "foo",
            "zds_documenttype_omschrijving_inzending": "foo",
            "zds_zaakdoc_vertrouwelijkheid": "GEHEIM",
        }

        hc_config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/"
            ),
            brp_personen_version=BRPVersions.v20,
        )
        hc_config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=hc_config,
        )

        global_config = GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        )
        global_config_patcher = patch(
            "openforms.config.models.GlobalConfiguration.get_solo",
            return_value=global_config,
        )

        hc_config = hc_config_patcher.start()
        global_config = global_config_patcher.start()
        cls.addClassCleanup(hc_config_patcher.stop)
        cls.addClassCleanup(global_config_patcher.stop)

    def test_create_zaak_with_one_form_step_and_children_as_betrokkene(self):
        """
        Input

        - Form step 1: children component
        - Children data: prefilled
        - Registration type: betrokkene
        - Children selection: disabled
        """

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "childrenKey",
                    "type": "children",
                    "label": "Children",
                    "enableSelection": False,
                    "registration": {"attribute": RegistrationAttribute.children},
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009969",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "childrenKey",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission)

        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        childrenKey_data = submission.data["childrenKey"]
        assert isinstance(childrenKey_data, list)

        for child in childrenKey_data:
            assert isinstance(child, dict)
            child.update(
                {
                    "selected": None,
                    "__id": str(uuid4()),
                    "__addedManually": False,
                }
            )

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[1]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)
        # make sure one child is present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            1,
        )
        # assert all the expected properties are present
        self.assertXPathEqualDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "000009969",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # child
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999993677",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Truus",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "T.",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Wiel",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "van der",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "19600912",
            },
        )

        # make sure that nothing is registered as extraElement
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.bsn']",
        )
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='children_immutable.0.bsn']",
        )

    def test_create_zaak_with_one_form_step_and_enabled_children_selection(
        self,
    ):
        """
        Input

        - Form step 1: children component
        - Children data: prefilled
        - Registration type: betrokkene
        - Children selection: enabled
        """

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "childrenKey",
                    "type": "children",
                    "label": "Children",
                    "enableSelection": True,
                    "registration": {"attribute": RegistrationAttribute.children},
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="999970094",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "childrenKey",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission)

        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        childrenKey_data = submission.data["childrenKey"]
        assert isinstance(childrenKey_data, list)
        assert isinstance(childrenKey_data[0], dict)
        assert isinstance(childrenKey_data[1], dict)

        childrenKey_data[0].update(
            {
                "selected": True,
                "__id": str(uuid4()),
                "__addedManually": False,
            }
        )
        childrenKey_data[1].update(
            {
                "selected": False,
                "__id": str(uuid4()),
                "__addedManually": False,
            }
        )

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[1]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)
        # make sure one child is present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            1,
        )
        # assert all the expected properties are present
        self.assertXPathEqualDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999970094",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # child
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999970100",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Olle",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "O.",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Oostingh",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20220202",
            },
        )

        # make sure that nothing is registered as extraElement
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.bsn']",
        )
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='children_immutable.0.bsn']",
        )

    def test_create_zaak_with_one_form_step_enabled_selection_and_manually_added_children(
        self,
    ):
        """
        Input

        - Form step 1: children component
        - Children data: manually added
        - Registration type: betrokkene
        - Children selection: enabled
        """

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "childrenKey",
                    "type": "children",
                    "label": "Children",
                    "enableSelection": True,
                    "registration": {"attribute": RegistrationAttribute.children},
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="123456782",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
            # apart from the extra frontend properties we have to mimic the manually added
            # children, that's why we pass the submitted data we get from the frontend
            submitted_data={
                "childrenKey": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                    {
                        "bsn": "999970161",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Peet",
                        "dateOfBirth": "2018-12-01",
                        "dateOfBirthPrecision": "date",
                        "selected": False,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "childrenKey",
                "min_age": None,
                "max_age": None,
            },
        )

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)

        # make sure one child is present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            1,
        )
        # assert all the expected properties are present
        self.assertXPathEqualDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "123456782",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # child
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999970409",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "N",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Pero",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "P.",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Paassen",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "van",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20230201",
            },
        )

        # make sure that nothing is registered as extraElement
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.bsn']",
        )
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='children_immutable.0.bsn']",
        )

    def test_create_zaak_with_one_form_step_disabled_selection_and_manually_added_children(
        self,
    ):
        """
        Input

        - Form step 1: children component
        - Children data: manually added
        - Registration type: betrokkene
        - Children selection: disabled
        """

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "childrenKey",
                    "type": "children",
                    "label": "Children",
                    "enableSelection": False,
                    "registration": {"attribute": RegistrationAttribute.children},
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="123456782",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
            # apart from the extra frontend properties we have to mimic the manually added
            # children, that's why we pass the submitted data we get from the frontend
            submitted_data={
                "childrenKey": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                    {
                        "bsn": "999970161",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Peet",
                        "dateOfBirth": "2018-12-01",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__id": str(uuid4()),
                        "__addedManually": True,
                    },
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "childrenKey",
                "min_age": None,
                "max_age": None,
            },
        )

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)

        # make sure two children are present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            2,
        )

        # assert all the expected properties are present
        self.assertXPathContainsDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "123456782",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # children
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": [
                    "999970409",
                    "999970161",
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": [
                    "N"
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": [
                    "Pero",
                    "Peet",
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "P.",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Paassen",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "van",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20181201",
            },
        )

        # make sure that nothing is registered as extraElement
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.bsn']",
        )
        self.assertXPathNotExists(
            xml_doc,
            "//stuf:extraElementen/stuf:extraElement[@naam='children_immutable.0.bsn']",
        )

    def test_create_zaak_with_one_form_step_and_children_as_extraelementen(self):
        """
        Input

        - Form step 1: children component
        - Children data: prefilled
        - Registration type: extraElementen
        - Children selection: disabled
        """

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "childrenKey",
                    "type": "children",
                    "label": "Children",
                    "enableSelection": False,
                },
            ],
            form__name="my-form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009969",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "childrenKey",
                "min_age": None,
                "max_age": None,
            },
        )

        prefill_variables(submission)

        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        childrenKey_data = submission.data["childrenKey"]
        assert isinstance(childrenKey_data, list)

        for child in childrenKey_data:
            assert isinstance(child, dict)
            child.update(
                {
                    "selected": None,
                    "__id": str(uuid4()),
                    "__addedManually": False,
                }
            )

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[1]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.bsn']": "999993677",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.firstNames']": "Truus",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.initials']": "T.",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.affixes']": "van der",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.lastName']": "Wiel",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.dateOfBirth']": "1960-09-12",
            },
        )

        # make sure that nothing is registered as zaakbetrokkene
        self.assertXPathNotExists(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
        )

    def test_create_zaak_with_two_form_steps_and_children_as_betrokkene(self):
        """
        Input

        - Form step 1: children component
        - Form step 2: editgrid component
        - Children data: prefilled
        - Registration type: betrokkene for children and extraElementen for editgrid
        - Children selection: disabled
        """

        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "label": "Children",
                        "enableSelection": False,
                        "registration": {"attribute": RegistrationAttribute.children},
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "extraChildDetails",
                        "components": [
                            {"type": "bsn", "key": "bsn", "label": "BSN"},
                            {
                                "type": "textfield",
                                "key": "childName",
                                "label": "Child name",
                            },
                        ],
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        submission = SubmissionFactory.create(
            form=form,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009969",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "children": [
                    {
                        "bsn": "999993677",
                        "affixes": "van der",
                        "initials": "T.",
                        "lastName": "Wiel",
                        "firstNames": "Truus",
                        "dateOfBirth": "1960-09-12",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__addedManually": False,
                        "__id": str(uuid4()),
                    }
                ]
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"extraChildDetails": [{"bsn": "999993677", "childName": "Truus"}]},
        )

        SubmissionReportFactory.create(submission=submission)

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)

        # assert children component of the first step (betrokkene)
        # make sure one child is present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            1,
        )
        # assert all the expected properties are present
        self.assertXPathEqualDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "000009969",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # child
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999993677",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Truus",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "T.",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Wiel",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorvoegselGeslachtsnaam": "van der",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "19600912",
            },
        )

        # assert editgrid component of the second step (extraElementen)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.bsn']": "999993677",
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.childName']": "Truus",
            },
        )

    def test_create_zaak_with_two_form_steps_and_children_as_extraElementen(self):
        """
        Input

        - Form step 1: children component
        - Form step 2: editgrid component
        - Children data: prefilled
        - Registration type: extraElementen for children and editgrid
        - Children selection: disabled
        """

        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "childrenKey",
                        "label": "Children",
                        "enableSelection": False,
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "extraChildDetails",
                        "components": [
                            {"type": "bsn", "key": "bsn", "label": "BSN"},
                            {
                                "type": "textfield",
                                "key": "childName",
                                "label": "Child name",
                            },
                        ],
                    }
                ]
            },
        )
        # not used, just for consistency-we do not use the prefill for the children here
        # because we have to inject the results in the submission steps
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "childrenKey",
                "min_age": None,
                "max_age": None,
            },
        )

        submission = SubmissionFactory.create(
            form=form,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="000009969",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "childrenKey": [
                    {
                        "bsn": "999993677",
                        "affixes": "van der",
                        "initials": "T.",
                        "lastName": "Wiel",
                        "firstNames": "Truus",
                        "dateOfBirth": "1960-09-12",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__addedManually": False,
                        "__id": str(uuid4()),
                    }
                ]
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"extraChildDetails": [{"bsn": "999993677", "childName": "Truus"}]},
        )

        SubmissionReportFactory.create(submission=submission)

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)
        self.assertXPathEqualDict(
            xml_doc,
            {
                # assert children component
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.initials']": "T.",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.affixes']": "van der",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.lastName']": "Wiel",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.dateOfBirth']": "1960-09-12",
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.bsn']": "999993677",
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.childName']": "Truus",
                # assert editgrid component
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.bsn']": "999993677",
                "//stuf:extraElementen/stuf:extraElement[@naam='childrenKey.0.firstNames']": "Truus",
            },
        )

    def test_create_zaak_with_two_form_steps_and_enabled_children_selection(
        self,
    ):
        """
        Input

        - Form step 1: children component
        - Form step 2: editgrid component
        - Children data: prefilled
        - Registration type: betrokkene for children and extraElementen for editgrid
        - Children selection: enabled
        """

        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "label": "Children",
                        "enableSelection": True,
                        "registration": {"attribute": RegistrationAttribute.children},
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "extraChildDetails",
                        "components": [
                            {"type": "bsn", "key": "bsn", "label": "BSN"},
                            {
                                "type": "textfield",
                                "key": "childName",
                                "label": "Child name",
                            },
                        ],
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        submission = SubmissionFactory.create(
            form=form,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="999970094",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "children": [
                    {
                        "bsn": "999970100",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Olle",
                        "dateOfBirth": "2022-02-02",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__addedManually": False,
                        "__id": str(uuid4()),
                    },
                    {
                        "bsn": "999970112",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Onne",
                        "dateOfBirth": "2022-02-02",
                        "dateOfBirthPrecision": "date",
                        "selected": False,
                        "__addedManually": False,
                        "__id": str(uuid4()),
                    },
                ],
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"extraChildDetails": [{"bsn": "999970100", "childName": "Olle"}]},
        )

        SubmissionReportFactory.create(submission=submission)

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)

        # assert children component of the first step (betrokkene)
        # make sure one child is present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            1,
        )
        # assert all the expected properties are present
        self.assertXPathEqualDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999970094",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # child
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999970100",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Olle",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "O.",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Oostingh",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20220202",
            },
        )

        # assert editgrid component of the second step (extraElementen)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.bsn']": "999970100",
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.childName']": "Olle",
            },
        )

    def test_create_zaak_with_two_form_steps_enabled_selection_and_manually_added_children(
        self,
    ):
        """
        Input

        - Form step 1: children component
        - Form step 2: editgrid component
        - Children data: manually added
        - Registration type: betrokkene for children and extraElementen for editgrid
        - Children selection: enabled
        """

        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "label": "Children",
                        "enableSelection": True,
                        "registration": {"attribute": RegistrationAttribute.children},
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "extraChildDetails",
                        "components": [
                            {"type": "bsn", "key": "bsn", "label": "BSN"},
                            {
                                "type": "textfield",
                                "key": "childName",
                                "label": "Child name",
                            },
                        ],
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        submission = SubmissionFactory.create(
            form=form,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="999970094",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "children": [
                    {
                        "bsn": "999970100",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Olle",
                        "dateOfBirth": "2022-02-02",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__addedManually": True,
                        "__id": str(uuid4()),
                    },
                    {
                        "bsn": "999970112",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Onne",
                        "dateOfBirth": "2022-02-02",
                        "dateOfBirthPrecision": "date",
                        "selected": False,
                        "__addedManually": True,
                        "__id": str(uuid4()),
                    },
                ],
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"extraChildDetails": [{"bsn": "999970100", "childName": "Olle"}]},
        )

        SubmissionReportFactory.create(submission=submission)

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)

        # assert children component of the first step (betrokkene)
        # make sure one child is present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            1,
        )
        # assert all the expected properties are present
        self.assertXPathEqualDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999970094",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # child
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999970100",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "N",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": "Olle",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "O.",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Oostingh",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20220202",
            },
        )

        # assert editgrid component of the second step (extraElementen)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.bsn']": "999970100",
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.childName']": "Olle",
            },
        )

    def test_create_zaak_with_two_form_steps_disabled_selection_and_manually_added_children(
        self,
    ):
        """
        Input

        - Form step 1: children component
        - Form step 2: editgrid component
        - Children data: manually added
        - Registration type: betrokkene for children and extraElementen for editgrid
        - Children selection: disabled
        """

        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "label": "Children",
                        "enableSelection": False,
                        "registration": {"attribute": RegistrationAttribute.children},
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "extraChildDetails",
                        "components": [
                            {"type": "bsn", "key": "bsn", "label": "BSN"},
                            {
                                "type": "textfield",
                                "key": "childName",
                                "label": "Child name",
                            },
                        ],
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        submission = SubmissionFactory.create(
            form=form,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="999970094",
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "1234"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "children": [
                    {
                        "bsn": "999970100",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Olle",
                        "dateOfBirth": "2022-02-02",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__addedManually": True,
                        "__id": str(uuid4()),
                    },
                    {
                        "bsn": "999970112",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Onne",
                        "dateOfBirth": "2022-02-02",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__addedManually": True,
                        "__id": str(uuid4()),
                    },
                ],
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={
                "extraChildDetails": [
                    {"bsn": "999970100", "childName": "Olle"},
                    {"bsn": "999970112", "childName": "Onne"},
                ]
            },
        )

        SubmissionReportFactory.create(submission=submission)

        self.plugin.register_submission(submission, self.options)
        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)

        self.assertSoapXMLCommon(xml_doc)

        # make sure two children are present
        self.assertXPathCount(
            xml_doc,
            "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn",
            2,
        )

        # assert all the expected properties are present
        self.assertXPathContainsDict(
            xml_doc,
            {
                # initiator
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": "999970094",
                "//zkn:object/zkn:heeftAlsInitiator/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": "J",
                # children
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:inp.bsn": [
                    "999970100",
                    "999970112",
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:authentiek": [
                    "N"
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voornamen": [
                    "Olle",
                    "Onne",
                ],
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:voorletters": "O.",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geslachtsnaam": "Oostingh",
                "//zkn:object/zkn:heeftAlsOverigBetrokkene[@stuf:entiteittype='ZAKBTROVR']/zkn:gerelateerde/zkn:natuurlijkPersoon/bg:geboortedatum": "20220202",
            },
        )

        # assert editgrid component of the second step (extraElementen)
        self.assertXPathEqualDict(
            xml_doc,
            {
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.bsn']": "999970100",
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.0.childName']": "Olle",
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.1.bsn']": "999970112",
                "//stuf:extraElementen/stuf:extraElement[@naam='extraChildDetails.1.childName']": "Onne",
            },
        )


class StufZDSConfirmationEmailVCRTests(OFVCRMixin, StUFZDSTestBase):
    VCR_TEST_FILES = TESTS_DIR / "files"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost/stuf-zds"
        )
        config = StufZDSConfig.get_solo()
        config.service = cls.zds_service
        config.save()
        cls.addClassCleanup(StufZDSConfig.clear_cache)

        cls.options: RegistrationOptions = {
            "zds_zaaktype_code": "foo",
            "zds_documenttype_omschrijving_inzending": "foo",
            "zds_zaakdoc_vertrouwelijkheid": "GEHEIM",
        }
        cls.submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textfield",
                    "type": "textfield",
                    "label": "textfield",
                },
            ],
            bsn="111222333",
            submitted_data={"textfield": "Foo"},
            language_code="en",
            public_registration_reference="abc123",
            registration_result={"zaak": "bar"},
            confirmation_email_sent=True,
        )

    @patch(
        "openforms.registrations.contrib.stuf_zds.plugin.get_last_confirmation_email",
        side_effect=[("HTML content 1", 1), ("HTML content 2", 2)],
    )
    def test_confirmation_emails_are_attached_when_updating_registration(
        self, mock_get_last_email
    ):
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        for _ in range(2):
            result = plugin.update_registration_with_confirmation_email(
                self.submission, self.options
            )
            assert result is not None

        self.assertEqual(len(result["intermediate"]["confirmation_emails"]), 2)

        # For each email: one for creating the document identifier one for attaching it
        self.assertEqual(len(self.cassette.requests), 4)

        for i in (-1, -3):
            stuf_request = self.cassette.requests[i]
            xml_doc = etree.fromstring(stuf_request.body)
            self.assertSoapXMLCommon(xml_doc)

            expected_items = {
                "titel": "Bevestigingsmail",
                "beschrijving": "De bevestigingsmail die naar de initiator is verstuurd.",
                "formaat": "application/pdf",
            }
            for name, value in expected_items.items():
                with self.subTest(extra_element=name, value=value):
                    self.assertXPathEqual(xml_doc, f"//zkn:object/zkn:{name}", value)

    @patch(
        "openforms.registrations.contrib.stuf_zds.plugin.get_last_confirmation_email",
        return_value=("HTML content", 1),
    )
    def test_confirmation_email_is_only_attached_once(self, mock_get_last_email):
        """
        Can occur when sending another confirmation email has failed for whatever
        reason.
        """
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        for _ in range(2):
            result = plugin.update_registration_with_confirmation_email(
                self.submission, self.options
            )
            assert result is not None

        self.assertEqual(len(result["intermediate"]["confirmation_emails"]), 1)

        # One for creating the first document identifier one for attaching it
        self.assertEqual(len(self.cassette.requests), 2)

    def test_updating_registration_skips_when_confirmation_email_was_not_sent(self):
        submission = SubmissionFactory.create(confirmation_email_sent=False)

        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        self.assertIsNone(
            plugin.update_registration_with_confirmation_email(submission, self.options)
        )

    @patch(
        "openforms.registrations.contrib.stuf_zds.plugin.get_last_confirmation_email",
        return_value=None,
    )
    def test_raises_when_confirmation_email_was_not_sent(self, mock_get_last_email):
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        plugin.register_submission(self.submission, self.options)

        with self.assertRaises(RegistrationFailed):
            plugin.update_registration_with_confirmation_email(
                self.submission, self.options
            )
