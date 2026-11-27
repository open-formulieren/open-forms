from pathlib import Path
from unittest.mock import patch

from django.test import tag

import requests_mock
import time_machine
from privates.test import temp_private_root

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormRegistrationBackendFactory
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin
from stuf.stuf_zds.models import StufZDSConfig
from stuf.stuf_zds.tests import StUFZDSTestBase
from stuf.stuf_zds.tests.utils import load_mock, match_text, xml_from_request_history
from stuf.tests.factories import StufServiceFactory

from ....exceptions import RegistrationFailed
from ....tasks import register_submission
from ..plugin import PLUGIN_IDENTIFIER, StufZDSRegistration
from ..typing import RegistrationOptions

TESTS_DIR = Path(__file__).parent.resolve()


@tag("gh-6919")
class IdempotencyTests(OFVCRMixin, StUFZDSTestBase):
    VCR_TEST_FILES = TESTS_DIR / "files"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost:82/stuf-zds"
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

    def test_pre_registering_twice_does_not_create_zaak_identificatie_again(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textfield",
                    "type": "textfield",
                    "label": "Textfield",
                },
            ],
            completed_not_preregistered=True,
            submitted_data={"textfield": "foo"},
        )

        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        plugin.pre_register_submission(submission, self.options)
        self.assertEqual(len(self.cassette.requests), 1)

        plugin.pre_register_submission(submission, self.options)
        self.assertEqual(len(self.cassette.requests), 1)

    def test_registering_twice_does_not_create_zaak_or_documents_again(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "key": "single_file",
                    "label": "Single file",
                    "file": {"type": []},
                    "filePattern": "",
                },
                {
                    "type": "file",
                    "key": "multiple_files",
                    "label": "Multiple files",
                    "file": {"type": []},
                    "filePattern": "",
                    "multiple": True,
                },
            ],
            completed_not_preregistered=True,
            with_report=True,
            # in this case, actual file data is not relevant for registration
            submitted_data={"single_file": [], "multiple_files": []},
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment1.jpg",
            submission_variable__key="single_file",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment2_1.jpg",
            submission_variable__key="multiple_files",
        )

        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)
        plugin.pre_register_submission(submission, self.options)
        plugin.register_submission(submission, self.options)
        # Breakdown:
        # 1. Create zaak identification (pre-registration)
        # 2. Create zaak
        # 3. Create document identification for submission report
        # 4. Create submission report document
        # 5. Create document identification for attachment 1
        # 6. Create attachment 1 document
        # 7. Create document identification for attachment 2
        # 8. Create attachment 2 document
        self.assertEqual(len(self.cassette.requests), 8)

        # Register again and ensure the number of requests stays the same
        plugin.register_submission(submission, self.options)
        self.assertEqual(len(self.cassette.requests), 8)


@tag("gh-1183")
@time_machine.travel("2020-12-22", tick=False)
@temp_private_root(reset_storage=False)
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
            with_report=True,
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
