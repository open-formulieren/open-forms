from collections.abc import Callable
from datetime import UTC, datetime
from unittest.mock import patch

from django.test import TestCase, tag

from privates.test import temp_private_root
from requests import RequestException
from vcr.request import Request as VCRRequest

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.contrib.zgw.clients.zaken import ZakenClient
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ....exceptions import RegistrationFailed
from ....tasks import register_submission
from .factories import ZGWApiGroupConfigFactory


class BeforeRecordRequestWrapper:
    hook: Callable[[VCRRequest], VCRRequest | None] | None = None

    def __call__(self, request: VCRRequest) -> VCRRequest | None:
        if hook := self.hook:
            return hook(request)
        return request


@tag("gh-1183")
@temp_private_root()
class PartialRegistrationFailureTests(OFVCRMixin, TestCase):
    """
    Test that partial results are stored and don't cause excessive registration calls.

    Issue #1183 -- case numbers are reserved to often, as a retry reserves a new one. It
    also happens that when certain other calls fail, a new Zaak is created which
    should not have been created again.
    """

    _vcr_before_record_request: BeforeRecordRequestWrapper = (
        BeforeRecordRequestWrapper()
    )
    """
    Instance variable to intercept and modify requests to introduce error behaviour.

    Set this in the test with a callback to introduce test-specific failure situations.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )

    def setUp(self):
        super().setUp()

        def _reset_vcr_hook():
            self._vcr_before_record_request.hook = None

        self.addCleanup(_reset_vcr_hook)

        # set up a simple form to track the partial result storing state
        self.submission = SubmissionFactory.from_components(
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
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
            form__name="my-form",
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": self.zgw_api_group.pk,
                "catalogue": {"domain": "TEST", "rsin": "000000000"},
                "case_type_identification": "ZT-001",
                "document_type_description": "Attachment Informatieobjecttype",
                "objects_api_group": None,
                "zaaktype": "",
                "informatieobjecttype": "",
                "organisatie_rsin": "000000000",
                "vertrouwelijkheidaanduiding": "",
            },
            completed_not_preregistered=True,
            bsn="111222333",
            # Pin to a known case & document type version
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
        )

    def _get_vcr_kwargs(self, **kwargs):
        kwargs["before_record_request"] = self._vcr_before_record_request
        return super()._get_vcr_kwargs(**kwargs)

    def test_failure_after_zaak_creation(self):
        submission = self.submission
        create_document_call_count = 0

        def fail_create_document_request(request: VCRRequest):
            if (
                request.url.startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten"
                )
                and request.method == "POST"
            ):
                nonlocal create_document_call_count
                create_document_call_count += 1
                raise RequestException("Server error")

            return request

        self._vcr_before_record_request.hook = fail_create_document_request

        with self.subTest("Initial document creation fails"):
            pre_registration(submission.pk, PostSubmissionEvents.on_completion)
            register_submission(submission.pk, PostSubmissionEvents.on_completion)

            submission.refresh_from_db()
            assert submission.registration_result
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = submission.registration_result["intermediate"]
            initially_created_zaak_url = intermediate_results["zaak"]["url"]
            self.assertTrue(
                initially_created_zaak_url.startswith(
                    "http://localhost:8003/zaken/api/v1/zaken/"
                )
            )
            self.assertIn("traceback", submission.registration_result)

        with self.subTest("New document creation attempt does not create zaak again"):
            with self.assertRaises(RegistrationFailed):
                register_submission(submission.pk, PostSubmissionEvents.on_retry)

            submission.refresh_from_db()
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = submission.registration_result["intermediate"]
            self.assertEqual(
                intermediate_results["zaak"]["url"], initially_created_zaak_url
            )
            self.assertIn("traceback", submission.registration_result)

        with self.subTest("verify request counts"):
            create_zaak_calls = [
                req
                for req in self.cassette.requests
                if req.method == "POST"
                if req.url == "http://localhost:8003/zaken/api/v1/zaken"
            ]
            self.assertEqual(len(create_zaak_calls), 1)
            self.assertEqual(create_document_call_count, 1 + 1)  # first attempt = retry

    def test_attachment_document_relation_create_fails(self):
        submission = self.submission
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="attachment1.jpg",
            form_key="field1",
        )

        relate_document_call_count = 0
        original_relate_document = ZakenClient.relate_document

        def wrapped_related_document(self, zaak, document):
            nonlocal relate_document_call_count
            relate_document_call_count += 1
            if (
                relate_document_call_count > 1
            ):  # let the PDF relation request go through
                raise RequestException("Simulted failure")
            return original_relate_document(self, zaak, document)

        with (
            self.subTest("First try, attachment relation fails"),
            patch.object(
                ZakenClient,
                "relate_document",
                autospec=True,
                side_effect=wrapped_related_document,
            ),
        ):
            pre_registration(submission.pk, PostSubmissionEvents.on_completion)
            register_submission(submission.pk, PostSubmissionEvents.on_completion)

            submission.refresh_from_db()
            assert submission.registration_result
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            self.assertIn("traceback", submission.registration_result)

            intermediate_results = submission.registration_result["intermediate"]
            initially_created_zaak_url = intermediate_results["zaak"]["url"]
            self.assertTrue(
                initially_created_zaak_url.startswith(
                    "http://localhost:8003/zaken/api/v1/zaken/"
                )
            )

            doc_report = intermediate_results["documents"]["report"]
            intially_created_doc_report_url = doc_report["document"]["url"]
            intially_created_doc_relation_url = doc_report["relation"]["url"]
            self.assertTrue(
                intially_created_doc_report_url.startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )

            doc_attachment = intermediate_results["documents"][str(attachment.pk)]
            initially_created_attachment_url = doc_attachment["document"]["url"]

            initially_created_initiator_rol_url = intermediate_results["initiator_rol"][
                "url"
            ]
            initially_created_status_url = intermediate_results["status"]["url"]

        with (
            self.subTest("New attempt - ensure existing data is not created again"),
            patch.object(
                ZakenClient,
                "relate_document",
                autospec=True,
                side_effect=wrapped_related_document,
            ),
        ):
            with self.assertRaises(RegistrationFailed):
                register_submission(submission.pk, PostSubmissionEvents.on_retry)

            submission.refresh_from_db()
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            intermediate_results = submission.registration_result["intermediate"]
            self.assertIn("traceback", submission.registration_result)

            self.assertEqual(
                intermediate_results["zaak"]["url"], initially_created_zaak_url
            )
            doc_report = intermediate_results["documents"]["report"]
            self.assertTrue(
                doc_report["document"]["url"].startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )
            self.assertTrue(
                doc_report["relation"]["url"].startswith(
                    "http://localhost:8003/zaken/api/v1/zaakinformatieobjecten/"
                )
            )

            doc_report = intermediate_results["documents"]["report"]
            self.assertEqual(
                doc_report["document"]["url"], intially_created_doc_report_url
            )
            self.assertEqual(
                doc_report["relation"]["url"], intially_created_doc_relation_url
            )

            doc_attachment = intermediate_results["documents"][str(attachment.pk)]
            self.assertEqual(
                doc_attachment["document"]["url"], initially_created_attachment_url
            )
            self.assertNotIn("relation", doc_attachment)

            self.assertEqual(
                intermediate_results["initiator_rol"]["url"],
                initially_created_initiator_rol_url,
            )
            self.assertEqual(
                intermediate_results["status"]["url"], initially_created_status_url
            )

    def test_zaakeigenschappen_creation_failure(self):
        submission = self.submission
        registration_backend = submission.form.registration_backends.get()
        registration_backend.options.update(
            {
                "property_mappings": [
                    {"component_key": "voornaam", "eigenschap": "a property name"}
                ],
            }
        )
        registration_backend.save()

        def fail_zaakeigenschappen_creation(request: VCRRequest):
            if (
                request.method == "POST"
                and request.url.startswith("http://localhost:8003/zaken/api/v1/zaken/")
                and request.url.endswith("zaakeigenschappen")
            ):
                raise RequestException("Server error")
            return request

        self._vcr_before_record_request.hook = fail_zaakeigenschappen_creation

        pre_registration(submission.pk, PostSubmissionEvents.on_completion)
        register_submission(submission.pk, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        assert submission.registration_result
        self.assertEqual(submission.registration_status, RegistrationStatuses.failed)
        self.assertIn("traceback", submission.registration_result)

        zt_eigenschappen = submission.registration_result["intermediate"][
            "zaaktype_eigenschappen"
        ]
        self.assertEqual(
            len(zt_eigenschappen), 2
        )  # 2 eigenschappen defined on the case type

    def test_failure_on_object_relation_zaakobject_creation(self):
        # no need to mock the failure - the host names in the compose setup already
        # genuinely break and cause validation issues :-)
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

        submission = self.submission
        registration_backend = submission.form.registration_backends.get()
        registration_backend.options.update(
            {
                "objects_api_group": objects_api_group.identifier,
                "objecttype": (
                    "http://host.docker.internal:8001/api/v2/"
                    "objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e"
                ),
                "objecttype_version": 1,
            }
        )
        registration_backend.save()

        pre_registration(submission.pk, PostSubmissionEvents.on_completion)
        register_submission(submission.pk, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        assert submission.registration_result
        self.assertEqual(submission.registration_status, RegistrationStatuses.failed)
        self.assertIn("traceback", submission.registration_result)

        intermediate_results = submission.registration_result["intermediate"]

        object_data = intermediate_results["objects_api_object"]
        self.assertTrue(
            object_data["url"].startswith("http://objects-web:8000/api/v2/objects/")
        )
