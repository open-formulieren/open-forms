from unittest.mock import patch

from django.test import TestCase

import requests_mock
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.factories import ServiceFactory

from openforms.registrations.contrib.objects_api.models import (
    ObjectsAPIRegistrationData,
    ObjectsAPISubmissionAttachment,
)
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ..models import ObjectsAPIConfig, ObjectsAPIGroupConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration


@requests_mock.Mocker()
class ObjectsAPIBackendTests(TestCase):
    """General tests for the Objects API registration backend.

    These tests don't depend on the options version (v1 or v2).
    """

    maxDiff = None

    def setUp(self):
        super().setUp()

        config = ObjectsAPIConfig(
            default_objects_api_group=ObjectsAPIGroupConfig(
                objects_service=ServiceFactory.build(
                    api_root="https://objecten.nl/api/v1/",
                    api_type=APITypes.orc,
                ),
                drc_service=ServiceFactory.build(
                    api_root="https://documenten.nl/api/v1/",
                    api_type=APITypes.drc,
                ),
            )
        )

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.plugin.ObjectsAPIConfig.get_solo",
            return_value=config,
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

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
                    "upload_submission_csv": True,
                    "informatieobjecttype_submission_csv": "dummy",
                },
            )

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertEqual(registration_data.pdf_url, "https://example.com")
        self.assertEqual(registration_data.csv_url, "")
