from unittest.mock import patch

from django.test import tag

import requests_mock
from freezegun import freeze_time
from privates.test import temp_private_root

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormRegistrationBackendFactory
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_zds.models import StufZDSConfig
from stuf.stuf_zds.tests import StUFZDSTestBase
from stuf.stuf_zds.tests.utils import load_mock, match_text, xml_from_request_history
from stuf.tests.factories import StufServiceFactory

from ....exceptions import RegistrationFailed
from ....tasks import register_submission


@tag("gh-1183")
@freeze_time("2020-12-22")
@temp_private_root()
class PartialRegistrationFailureTests(StUFZDSTestBase):
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
        cls.config_patcher = patch(
            "openforms.registrations.contrib.stuf_zds.plugin.StufZDSConfig.get_solo",
            return_value=StufZDSConfig(service=cls.service),
        )
        cls.general_config_patcher = patch(
            "openforms.plugins.plugin.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                plugin_configuration={
                    "registration": {
                        "stuf_zds": {"enabled": True},
                    },
                }
            ),
        )

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
            completed_not_preregistered=True,
            bsn="111222333",
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
        )
        FormRegistrationBackendFactory.create(
            form=cls.submission.form,
            backend="stuf-zds-create-zaak",
            options={
                "zds_zaaktype_code": "zt-code",
                "zds_zaaktype_status_code": "123",
                "zds_documenttype_omschrijving_inzending": "aaabbc",
            },
        )

    def setUp(self):
        super().setUp()

        self.config_patcher.start()
        self.addCleanup(self.config_patcher.stop)

        self.general_config_patcher.start()
        self.addCleanup(self.general_config_patcher.stop)

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

        pre_registration(self.submission.id, PostSubmissionEvents.on_completion)
        register_submission(self.submission.id, PostSubmissionEvents.on_completion)
        with self.subTest("Initial registration fails"):
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
                register_submission(self.submission.id, PostSubmissionEvents.on_retry)

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

        pre_registration(self.submission.id, PostSubmissionEvents.on_completion)
        register_submission(self.submission.id, PostSubmissionEvents.on_completion)
        with self.subTest("Document id generation fails"):
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
                register_submission(self.submission.id, PostSubmissionEvents.on_retry)

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

        pre_registration(self.submission.id, PostSubmissionEvents.on_completion)
        register_submission(self.submission.id, PostSubmissionEvents.on_completion)
        with self.subTest("Document id generation fails"):
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
                register_submission(self.submission.id, PostSubmissionEvents.on_retry)

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
