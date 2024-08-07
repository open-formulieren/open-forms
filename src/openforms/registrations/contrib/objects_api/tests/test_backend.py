from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase

import requests_mock
from zgw_consumers.test import generate_oas_component

from openforms.contrib.objects_api.helpers import prepare_data_for_registration
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
from openforms.utils.tests.vcr import OFVCRMixin

from ..client import get_objects_client
from ..models import ObjectsAPIConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from .factories import ObjectsAPIGroupConfigFactory


@requests_mock.Mocker()
class ObjectsAPIBackendTests(TestCase):
    """General tests for the Objects API registration backend.

    These tests don't depend on the options version (v1 or v2).
    """

    maxDiff = None

    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=ObjectsAPIConfig(),
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
        )

    def test_csv_creation_fails_pdf_still_saved(self, m: requests_mock.Mocker):
        """Test the behavior when one of the API calls fails.

        The exception should be caught, the intermediate data saved, and a
        ``RegistrationFailed`` should be raised in the end.
        """

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                },
            ],
            submitted_data={"voornaam": "Foo"},
        )

        pdf = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )

        # OK on PDF request
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=pdf,
            additional_matcher=lambda req: req.json()["bestandsnaam"].endswith(".pdf"),
        )

        # Failure on CSV request (which is dispatched after the PDF one)
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=500,
            additional_matcher=lambda req: "csv" in req.json()["bestandsnaam"],
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(
                submission,
                {
                    "objects_api_group": self.objects_api_group,
                    "upload_submission_csv": True,
                    "informatieobjecttype_submission_csv": "dummy",
                    "informatieobjecttype_submission_report": "dummy",
                },
            )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertEqual(registration_data.pdf_url, pdf["url"])
        self.assertEqual(registration_data.csv_url, "")

    def test_attachment_fails_other_attachments_still_saved(
        self, m: requests_mock.Mocker
    ):
        """Test the behavior when one of the API calls to register an attachment fails.

        The exception should be caught, the first attachment saved, and a
        ``RegistrationFailed`` should be raised in the end.
        """

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

        jpg_resp = generate_oas_component(
            "documenten",
            "schemas/EnkelvoudigInformatieObject",
            url="https://documenten.nl/api/v1/enkelvoudiginformatieobjecten/1",
        )

        # OK on JPG attachment request
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=201,
            json=jpg_resp,
            additional_matcher=lambda req: req.json()["bestandsnaam"].endswith(".jpg"),
        )

        # Failure on PNG attachment request (which is dispatched after the JPG one)
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=500,
            additional_matcher=lambda req: req.json()["bestandsnaam"].endswith(".png"),
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(
                submission,
                {
                    "objects_api_group": self.objects_api_group,
                    "upload_submission_csv": False,
                    "informatieobjecttype_attachment": "dummy",
                },
            )

        attachment = ObjectsAPISubmissionAttachment.objects.filter(
            submission_file_attachment=attachment_1
        )
        self.assertTrue(attachment.exists())

    def test_registration_works_after_failure(self, m: requests_mock.Mocker):
        """Test the registration behavior after a failure.

        As a ``ObjectsAPIRegistrationData`` instance was already created, it shouldn't crash.
        """

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornaam",
                    "type": "textfield",
                },
            ],
            submitted_data={"voornaam": "Foo"},
        )

        # Instance created from a previous attempt
        registration_data = ObjectsAPIRegistrationData.objects.create(
            submission=submission, pdf_url="https://example.com"
        )

        # Failure on CSV request (no mocks for the PDF one, we assume it was already created)
        m.post(
            "https://documenten.nl/api/v1/enkelvoudiginformatieobjecten",
            status_code=500,
            additional_matcher=lambda req: "csv" in req.json()["bestandsnaam"],
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.assertRaises(RegistrationFailed):
            plugin.register_submission(
                submission,
                {
                    "objects_api_group": self.objects_api_group,
                    "upload_submission_csv": True,
                    "informatieobjecttype_submission_csv": "dummy",
                },
            )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertEqual(registration_data.pdf_url, "https://example.com")
        self.assertEqual(registration_data.csv_url, "")


class ObjectsAPIBackendVCRTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=ObjectsAPIConfig(),
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

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
                },
            )

            assert object_create_result3

            self.assertEqual(
                object_create_result3["record"]["data"]["data"]["fd-test"]["voornaam"],
                "Updated value",
            )
            self.assertNotEqual(object_create_result3["uuid"], created_obj["uuid"])
