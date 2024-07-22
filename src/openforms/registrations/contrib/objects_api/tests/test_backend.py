from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase

import requests_mock
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.factories import ServiceFactory

from openforms.registrations.constants import RegistrationAttribute
from openforms.registrations.contrib.objects_api.models import (
    ObjectsAPIRegistrationData,
    ObjectsAPISubmissionAttachment,
)
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ObjectsAPIConfig, ObjectsAPIGroupConfig
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

        self.objects_api_group = ObjectsAPIGroupConfig.objects.create(
            objecttypes_service=ServiceFactory.create(
                api_root="http://localhost:8001/api/v2/",
                api_type=APITypes.orc,
                oas="https://example.com/",
                header_key="Authorization",
                # See the docker compose fixtures:
                header_value="Token 171be5abaf41e7856b423ad513df1ef8f867ff48",
                auth_type=AuthTypes.api_key,
            ),
            objects_service=ServiceFactory.create(
                api_root="http://localhost:8002/api/v2/",
                api_type=APITypes.orc,
                oas="https://example.com/",
                header_key="Authorization",
                # See the docker compose fixtures:
                header_value="Token 7657474c3d75f56ae0abd0d1bf7994b09964dca9",
                auth_type=AuthTypes.api_key,
            ),
            drc_service=ServiceFactory.create(
                api_root="http://localhost:8003/documenten/api/v1/",
                api_type=APITypes.drc,
                # See the docker compose fixtures:
                client_id="test_client_id",
                secret="test_secret_key",
                auth_type=AuthTypes.zgw,
            ),
            catalogi_service=ServiceFactory.create(
                api_root="http://localhost:8003/catalogi/api/v1/",
                api_type=APITypes.ztc,
                # See the docker compose fixtures:
                client_id="test_client_id",
                secret="test_secret_key",
                auth_type=AuthTypes.zgw,
            ),
        )

    def test_submission_with_objects_api_backend_create_and_update_object(self):
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with self.subTest("Create an object"):
            submission_create = SubmissionFactory.from_components(
                [
                    {
                        "key": "voornaam",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_voornamen,
                        },
                    },
                ],
                submitted_data={"voornaam": "Foo"},
                form_definition_kwargs={"slug": "fd-create"},
            )
            object_create_result = plugin.register_submission(
                submission_create,
                {
                    "version": 1,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "objects_api_group": self.objects_api_group,
                    "update_existing_object": False,
                },
            )

            assert object_create_result

            self.assertEqual(
                object_create_result["record"]["data"]["data"]["fd-create"]["voornaam"],
                "Foo",
            )

        with self.subTest("Update the above existing object"):
            submission_update = SubmissionFactory.from_components(
                [
                    {
                        "key": "voornaam",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_voornamen,
                        },
                    },
                ],
                submitted_data={"voornaam": "Updated value"},
                form_definition_kwargs={"slug": "fd-update1"},
                initial_data_reference=object_create_result["uuid"],
            )
            object_update_result = plugin.register_submission(
                submission_update,
                {
                    "version": 1,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "objects_api_group": self.objects_api_group,
                    "update_existing_object": True,
                },
            )

            assert object_update_result

            self.assertEqual(
                object_update_result["record"]["data"]["data"]["fd-update1"][
                    "voornaam"
                ],
                "Updated value",
            )
            self.assertEqual(object_update_result["uuid"], object_create_result["uuid"])

        with self.subTest(
            "Existing object not updated when update_existing_object=False"
        ):
            submission_update2 = SubmissionFactory.from_components(
                [
                    {
                        "key": "voornaam",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_voornamen,
                        },
                    },
                ],
                submitted_data={"voornaam": "Updated value"},
                form_definition_kwargs={"slug": "fd-update2"},
                initial_data_reference="095be615-a8ad-4c33-8e9c-c7612fbf6c9f",
            )
            object_create_result2 = plugin.register_submission(
                submission_update2,
                {
                    "version": 1,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "objects_api_group": self.objects_api_group,
                    "update_existing_object": False,
                },
            )

            assert object_create_result2

            self.assertEqual(
                object_create_result2["record"]["data"]["data"]["fd-update2"][
                    "voornaam"
                ],
                "Updated value",
            )
            self.assertNotEqual(
                object_create_result2["uuid"], object_create_result["uuid"]
            )

        with self.subTest("Existing object not updated when no data reference"):
            submission_update2 = SubmissionFactory.from_components(
                [
                    {
                        "key": "voornaam",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_voornamen,
                        },
                    },
                ],
                submitted_data={"voornaam": "Updated value"},
                form_definition_kwargs={"slug": "fd-update3"},
                initial_data_reference="",
            )
            object_create_result3 = plugin.register_submission(
                submission_update2,
                {
                    "version": 1,
                    "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
                    "objecttype_version": 3,
                    "objects_api_group": self.objects_api_group,
                    "update_existing_object": True,
                },
            )

            assert object_create_result3

            self.assertEqual(
                object_create_result3["record"]["data"]["data"]["fd-update3"][
                    "voornaam"
                ],
                "Updated value",
            )
            self.assertNotEqual(
                object_create_result3["uuid"], object_create_result["uuid"]
            )
