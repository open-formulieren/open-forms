from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase

from requests import RequestException
from vcr.request import Request as VCRRequest

from openforms.contrib.objects_api.clients import (
    get_documents_client,
    get_objects_client,
)
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.formio.tests.factories import SubmittedFileFactory
from openforms.forms.tests.factories import FormFactory
from openforms.registrations.contrib.objects_api.models import (
    ObjectsAPIRegistrationData,
    ObjectsAPISubmissionAttachment,
)
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionStepFactory,
)
from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ObjectsAPIConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from ..typing import RegistrationOptionsV2


class BeforeRecordRequestWrapper:
    hook: Callable[[VCRRequest], VCRRequest | None] | None = None

    def __call__(self, request: VCRRequest) -> VCRRequest | None:
        if hook := self.hook:
            return hook(request)
        return request


class ObjectsAPIBackendVCRTests(OFVCRMixin, TestCase):
    _vcr_before_record_request: BeforeRecordRequestWrapper = (
        BeforeRecordRequestWrapper()
    )
    """
    Instance variable to intercept and modify requests to introduce error behaviour.

    Set this in the test with a callback to introduce test-specific failure situations.
    """

    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=ObjectsAPIConfig(),
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

        def _reset_vcr_hook():
            self._vcr_before_record_request.hook = None

        self.addCleanup(_reset_vcr_hook)

    def _get_vcr_kwargs(self, **kwargs):
        kwargs["before_record_request"] = self._vcr_before_record_request
        return super()._get_vcr_kwargs(**kwargs)

    def test_csv_creation_fails_pdf_still_saved(self):
        """Test the behavior when one of the API calls fails.

        The exception should be caught, the intermediate data saved, and a
        ``RegistrationFailed`` should be raised in the end.
        """

        def fail_csv_request(request: VCRRequest):
            if not request.url.startswith("http://localhost:8003/documenten/api/v1"):
                return request
            if request.method != "POST":
                return request

            assert isinstance(request.body, bytes)
            request_body = json.loads(request.body)

            if request_body["bestandsnaam"].endswith(".csv"):
                raise RequestException("Broken CSV upload.")
            else:
                return request

        self._vcr_before_record_request.hook = fail_csv_request
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            organisatie_rsin="000000000",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                },
            ],
            submitted_data={"voornaam": "Foo"},
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 7, 1, 12, 0, 0).replace(tzinfo=UTC),
        )

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(
                submission,
                {
                    "version": 1,
                    "objects_api_group": objects_api_group,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "iot_submission_report": "PDF Informatieobjecttype",
                    "iot_submission_csv": "CSV Informatieobjecttype",
                    "iot_attachment": "",
                    "upload_submission_csv": True,
                    "update_existing_object": False,
                    "auth_attribute_path": [],
                },
            )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertTrue(
            registration_data.pdf_url.startswith(
                "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten"
            )
        )
        self.assertEqual(registration_data.csv_url, "")

    def test_attachment_fails_other_attachments_still_saved(self):
        """Test the behavior when one of the API calls to register an attachment fails.

        The exception should be caught, the first attachment saved, and a
        ``RegistrationFailed`` should be raised in the end.
        """

        def fail_ping_request(request: VCRRequest):
            if not request.url.startswith("http://localhost:8003/documenten/api/v1"):
                return request
            if request.method != "POST":
                return request

            assert isinstance(request.body, bytes)
            request_body = json.loads(request.body)

            if request_body["bestandsnaam"].endswith(".png"):
                raise RequestException("Broken PNG upload.")
            else:
                return request

        self._vcr_before_record_request.hook = fail_ping_request
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            organisatie_rsin="000000000",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "file_1",
                    "type": "file",
                },
                {
                    "key": "file_2",
                    "type": "file",
                },
            ],
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 7, 1, 12, 0, 0).replace(tzinfo=UTC),
        )
        submission_step = submission.steps[0]
        attachment_1 = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment1.jpg",
            form_key="file_1",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment2.png",
            form_key="file_2",
        )

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(
                submission,
                {
                    "version": 1,
                    "objects_api_group": objects_api_group,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "iot_attachment": "Attachment Informatieobjecttype",
                    "iot_submission_report": "",
                    "iot_submission_csv": "",
                    "upload_submission_csv": False,
                },
            )

        attachment = ObjectsAPISubmissionAttachment.objects.filter(
            submission_file_attachment=attachment_1
        )
        self.assertTrue(attachment.exists())

    def test_registration_works_after_failure(self):
        """Test the registration behavior after a failure.

        If an ``ObjectsAPIRegistrationData`` instance was already created, it shouldn't
        cause crashes when retrying.
        """

        def fail_csv_request(request: VCRRequest):
            if not request.url.startswith("http://localhost:8003/documenten/api/v1"):
                return request
            if request.method != "POST":
                return request

            assert isinstance(request.body, bytes)
            request_body = json.loads(request.body)

            if request_body["bestandsnaam"].endswith(".csv"):
                raise RequestException("Broken CSV upload.")
            else:
                return request

        self._vcr_before_record_request.hook = fail_csv_request
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            organisatie_rsin="000000000",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                },
            ],
            submitted_data={"voornaam": "Foo"},
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 7, 1, 12, 0, 0).replace(tzinfo=UTC),
        )
        # Instance created from a previous attempt
        registration_data = ObjectsAPIRegistrationData.objects.create(
            submission=submission,
            pdf_url="https://example.com",
        )

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(
                submission,
                {
                    "version": 1,
                    "objects_api_group": objects_api_group,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "iot_submission_report": "",
                    "iot_submission_csv": "CSV Informatieobjecttype",
                    "iot_attachment": "",
                    "upload_submission_csv": True,
                    "update_existing_object": False,
                    "auth_attribute_path": [],
                },
            )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )
        self.assertEqual(registration_data.pdf_url, "https://example.com")
        self.assertEqual(registration_data.csv_url, "")

    def test_submission_with_objects_api_backend_create_and_update_object(self):
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__slug="fd-test",
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "voornaam",
                        "label": "Voornaam",
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()

        # We manually create the objects instance as if it was created upfront by some external party
        with get_objects_client(objects_api_group) as client:
            created_obj = client.create_object(
                record_data=prepare_data_for_registration(
                    data={
                        "name": {
                            "voornaam": "My last name",
                        },
                    },
                    objecttype_version=3,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )

        with self.subTest("Create an object"):
            submission_create = SubmissionFactory.create(form=form, completed=True)
            SubmissionStepFactory.create(
                submission=submission_create,
                form_step=form_step,
                data={"voornaam": "My last name"},
            )
            object_create_result = plugin.register_submission(
                submission_create,
                {
                    "version": 1,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "objects_api_group": objects_api_group,
                    "update_existing_object": False,
                    "auth_attribute_path": [],
                },
            )

            assert object_create_result is not None

            self.assertNotEqual(object_create_result["uuid"], created_obj["uuid"])
            self.assertEqual(
                object_create_result["record"]["data"]["data"]["fd-test"]["voornaam"],
                "My last name",
            )

        with self.subTest("Update existing object"):
            submission_update = SubmissionFactory.create(
                form=form,
                completed=True,
                initial_data_reference=created_obj["uuid"],
            )
            SubmissionStepFactory.create(
                submission=submission_update,
                form_step=form_step,
                data={"voornaam": "Updated value"},
            )
            object_update_result = plugin.register_submission(
                submission_update,
                {
                    "version": 1,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "objects_api_group": objects_api_group,
                    "update_existing_object": True,
                    "auth_attribute_path": ["bsn"],
                },
            )

            assert object_update_result

            with get_objects_client(objects_api_group) as client:
                obj_retrieved = client.get_object(object_uuid=created_obj["uuid"])

            self.assertEqual(
                obj_retrieved["record"]["data"]["data"]["fd-test"]["voornaam"],
                "Updated value",
            )
            self.assertEqual(obj_retrieved["uuid"], object_update_result["uuid"])

        with self.subTest(
            "Existing object not updated when update_existing_object=False"
        ):
            submission_update2 = SubmissionFactory.create(
                form=form,
                completed=True,
                initial_data_reference=created_obj["uuid"],
            )
            SubmissionStepFactory.create(
                submission=submission_update2,
                form_step=form_step,
                data={"voornaam": "Updated value"},
            )

            object_create_result2 = plugin.register_submission(
                submission_update2,
                {
                    "version": 1,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "objects_api_group": objects_api_group,
                    "update_existing_object": False,
                    "auth_attribute_path": [],
                },
            )

            assert object_create_result2

            self.assertEqual(
                object_create_result2["record"]["data"]["data"]["fd-test"]["voornaam"],
                "Updated value",
            )
            self.assertNotEqual(object_create_result2["uuid"], created_obj["uuid"])

        with self.subTest("Existing object not updated when no data reference"):
            submission_update3 = SubmissionFactory.create(
                form=form, completed=True, initial_data_reference=""
            )
            SubmissionStepFactory.create(
                submission=submission_update3,
                form_step=form_step,
                data={"voornaam": "Updated value"},
            )

            object_create_result3 = plugin.register_submission(
                submission_update3,
                {
                    "version": 1,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "objects_api_group": objects_api_group,
                    "update_existing_object": True,
                    "auth_attribute_path": ["bsn"],
                },
            )

            assert object_create_result3

            self.assertEqual(
                object_create_result3["record"]["data"]["data"]["fd-test"]["voornaam"],
                "Updated value",
            )
            self.assertNotEqual(object_create_result3["uuid"], created_obj["uuid"])

    def test_prefer_dynamic_resolution_over_fixed_url(self):
        # If both the description and URL of a document type are provided, prefer the
        # description.

        # this one belongs to catalogue OTHER instead of TEST
        doctype_to_ignore = (
            "http://localhost:8003/catalogi/api/v1/"
            "informatieobjecttypen/d1cfb1d8-8593-4814-919d-72e38e80388f"
        )
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            organisatie_rsin="000000000",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "attachment",
                    "type": "file",
                }
            ],
            submitted_data={
                "attachment": [SubmittedFileFactory.build()],
            },
            completed=True,
            # Use a stable timestamp to get stable request params
            completed_on=datetime(2024, 7, 1, 12, 0, 0).replace(tzinfo=UTC),
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="attachment1.jpg",
            form_key="attachment",
            content_type="application/octet-stream",
        )
        # version is not relevant, works the same for v1
        options = {
            "version": 2,
            "objects_api_group": api_group,
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "attachment",
                    "target_path": ["single_file"],
                },
            ],
            "upload_submission_csv": True,
            "transform_to_list": [],
        }

        for suffix in ("attachment", "submission_report", "submission_csv"):
            with self.subTest(document=suffix):
                attachment.file_name = suffix
                attachment.save()

                result = plugin.register_submission(
                    submission,
                    {
                        **options,
                        f"iot_{suffix}": "PDF Informatieobjecttype",
                        f"informatieobjecttype_{suffix}": doctype_to_ignore,
                    },
                )

                assert result is not None
                document_url = result["record"]["data"]["single_file"]
                with get_documents_client(api_group) as client:
                    created_document = client.get(document_url).json()

                document_type = created_document["informatieobjecttype"]
                self.assertNotEqual(document_type, doctype_to_ignore)

    def test_create_document_documenttype_dynamically_resolved(self):
        """
        Test the behaviour when using dynamic resolution of document types.
        """
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
            organisatie_rsin="000000000",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "attachment",
                    "type": "file",
                }
            ],
            submitted_data={
                "attachment": [SubmittedFileFactory.build()],
            },
            completed=True,
            # version 531f6c1a-97f7-478c-85f0-67d2f23661c7 of the document type is
            # valid on this timestamp
            completed_on=datetime(2024, 7, 1, 12, 0, 0).replace(tzinfo=UTC),
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="attachment1.jpg",
            form_key="attachment",
        )

        # version is not relevant, works the same for v1
        options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": api_group,
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "attachment",
                    "target_path": ["single_file"],
                },
            ],
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "Attachment Informatieobjecttype",
            "transform_to_list": [],
        }

        result = plugin.register_submission(submission, options)

        assert result is not None

        document_url = result["record"]["data"]["single_file"]
        with get_documents_client(api_group) as client:
            created_document = client.get(document_url).json()

        self.assertEqual(
            created_document["informatieobjecttype"],
            (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
        )

    @enable_feature_flag("ZGW_APIS_INCLUDE_DRAFTS")
    def test_allow_registration_with_unpublished_document_types(self):
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="DRAFT",
            catalogue_rsin="000000000",
            organisatie_rsin="000000000",
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "attachment",
                    "type": "file",
                }
            ],
            submitted_data={
                "attachment": [SubmittedFileFactory.build()],
            },
            completed=True,
            # version is valid from August 9th
            completed_on=datetime(2024, 8, 10, 12, 0, 0).replace(tzinfo=UTC),
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            file_name="attachment1.jpg",
            form_key="attachment",
        )

        # version is not relevant, works the same for v1
        options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": api_group,
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "attachment",
                    "target_path": ["single_file"],
                },
            ],
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "Unpublished",
            "transform_to_list": [],
        }

        result = plugin.register_submission(submission, options)

        assert result is not None
        document_url = result["record"]["data"]["single_file"]
        with get_documents_client(api_group) as client:
            created_document = client.get(document_url).json()

        self.assertEqual(
            created_document["informatieobjecttype"],
            (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/3628d25f-f491-4375-a752-39d16bf2dd59"
            ),
        )
