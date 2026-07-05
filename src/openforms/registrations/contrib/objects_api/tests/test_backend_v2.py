from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID, uuid4

from django.test import TestCase, tag
from django.utils import timezone

from freezegun import freeze_time
from privates.test import temp_private_root
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.authentication.service import AuthAttribute
from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.contrib.objects_api.clients import get_documents_client
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.formio.tests.factories import SubmittedFileFactory
from openforms.forms.tests.factories import FormVariableFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.prefill.contrib.family_members.plugin import (
    PLUGIN_IDENTIFIER as FM_PLUGIN_IDENTIFIER,
)
from openforms.prefill.service import prefill_variables
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tasks import pre_registration
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ....constants import RegistrationAttribute
from ..config import ObjectsAPIOptionsSerializer
from ..constants import PLUGIN_IDENTIFIER
from ..models import (
    ObjectsAPIRegistrationData,
    ObjectsAPISubmissionAttachment,
)
from ..plugin import ObjectsAPIRegistration
from ..submission_registration import ObjectsAPIV2Handler
from ..typing import RegistrationOptionsV2


@temp_private_root()
class ObjectsAPIBackendV2Tests(OFVCRMixin, TestCase):
    """This test case requires the Objects & Objecttypes API and Open Zaak to be running.

    See the relevant Docker compose in the ``docker/`` folder.
    """

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    @freeze_time("2026-06-25T18:07:00+00:00")
    def test_register_with_mapping_and_objecttype_and_document_types_resolve(self):
        submission = SubmissionFactory.from_components(
            [
                {"key": "age", "type": "number"},
                {"key": "lastname", "type": "textfield"},
                {"key": "location", "type": "map"},
            ],
            completed=True,
            submitted_data={
                "age": 20,
                "lastname": "My last name",
                "location": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 3, 19, 13, 40, 34).replace(tzinfo=UTC),
            with_report=True,
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "catalogue": {"domain": "TEST", "rsin": "000000000"},
            "iot_submission_report": "PDF Informatieobjecttype",
            "iot_submission_csv": "CSV Informatieobjecttype",
            "iot_attachment": "Attachment Informatieobjecttype",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                {
                    "variable_key": "age",
                    "target_path": ["age"],
                },
                {"variable_key": "lastname", "target_path": ["name", "last.name"]},
                {
                    "variable_key": "now",
                    "target_path": ["submission_date"],
                },
                {
                    "variable_key": "pdf_url",
                    "target_path": ["submission_pdf_url"],
                },
                {
                    "variable_key": "csv_url",
                    "target_path": ["submission_csv_url"],
                },
                {
                    "variable_key": "payment_completed",
                    "target_path": ["submission_payment_completed"],
                },
                {
                    "variable_key": "payment_amount",
                    "target_path": ["submission_payment_amount"],
                },
                {
                    "variable_key": "payment_public_order_ids",
                    "target_path": ["submission_payment_public_ids"],
                },
                {
                    "variable_key": "cosign_date",
                    "target_path": ["cosign_date"],
                },
            ],
            "geometry_variable_key": "location",
            "transform_to_list": [],
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        assert result is not None
        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        with self.subTest("objects API record"):
            self.assertEqual(
                result["type"],
                "http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )
            self.assertEqual(
                result["record"]["typeVersion"], v2_options["objecttype_version"]
            )
            submission_date = (
                timezone.now().replace(second=0, microsecond=0).isoformat()
            )
            self.assertEqual(
                result["record"]["data"],
                {
                    "age": 20,
                    "cosign_date": None,
                    "name": {
                        "last.name": "My last name",
                    },
                    "submission_pdf_url": registration_data.pdf_url,
                    "submission_csv_url": registration_data.csv_url,
                    "submission_payment_completed": False,
                    "submission_payment_amount": None,
                    "submission_payment_public_ids": [],
                    "submission_date": submission_date,
                },
            )
            self.assertEqual(
                result["record"]["geometry"],
                {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            )

        with (
            self.subTest("document types"),
            get_documents_client(self.objects_api_group) as client,
        ):
            csv_document = client.get(registration_data.csv_url).json()
            pdf_document = client.get(registration_data.pdf_url).json()

            self.assertEqual(
                csv_document["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
            )

            self.assertEqual(
                pdf_document["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
            )

    def test_payment_attributes_mapping(self):
        submission = SubmissionFactory.create(completed=True)

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": False,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "payment_completed",
                    "target_path": ["submission_payment_completed"],
                },
                {
                    "variable_key": "payment_amount",
                    "target_path": ["submission_payment_amount"],
                },
                {
                    "variable_key": "payment_public_order_ids",
                    "target_path": ["submission_payment_public_ids"],
                },
                {
                    "variable_key": "provider_payment_ids",
                    "target_path": ["submission_provider_payment_ids"],
                },
            ],
            "transform_to_list": [],
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        submission.price = Decimal("40.00")
        submission.save()
        SubmissionPaymentFactory.create(
            submission=submission,
            amount=Decimal("25.00"),
            public_order_id="foo",
            status=PaymentStatus.completed,
            provider_payment_id="123456",
        )
        SubmissionPaymentFactory.create(
            submission=submission,
            amount=Decimal("15.00"),
            public_order_id="bar",
            status=PaymentStatus.registered,
            provider_payment_id="654321",
        )
        # failed payment, should be ignored
        SubmissionPaymentFactory.create(
            submission=submission,
            amount=Decimal("15.00"),
            public_order_id="baz",
            status=PaymentStatus.failed,
            provider_payment_id="6789",
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        assert result is not None
        data = result["record"]["data"]
        self.assertEqual(data["submission_payment_completed"], True)
        self.assertEqual(data["submission_payment_amount"], 40.0)
        self.assertEqual(data["submission_payment_public_ids"], ["foo", "bar"])
        self.assertEqual(data["submission_provider_payment_ids"], ["123456", "654321"])

    def test_upload_attachments_from_file_components(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "key": "single_file",
                    "label": "single_file",
                    "file": {"type": []},
                    "filePattern": "",
                },
                {
                    "type": "file",
                    "key": "multiple_files",
                    "label": "multiple_files",
                    "file": {"type": []},
                    "filePattern": "",
                    "multiple": True,
                },
            ],
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 3, 19, 13, 40, 34).replace(tzinfo=UTC),
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
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "catalogue": {"domain": "TEST", "rsin": "000000000"},
            "iot_attachment": "Attachment Informatieobjecttype",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                {
                    "variable_key": "single_file",
                    "target_path": ["single_file"],
                },
                {
                    "variable_key": "multiple_files",
                    "target_path": ["multiple_files"],
                },
            ],
            "transform_to_list": [],
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        assert result is not None
        with self.subTest("file values mapping"):
            self.assertTrue(
                result["record"]["data"]["single_file"].startswith(
                    "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
                )
            )
            self.assertIsInstance(result["record"]["data"]["multiple_files"], list)
            self.assertEqual(len(result["record"]["data"]["multiple_files"]), 1)

        with (
            self.subTest("document type resolution"),
            get_documents_client(self.objects_api_group) as client,
        ):
            attachment_1 = client.get(result["record"]["data"]["single_file"]).json()
            attachment_2_1 = client.get(
                result["record"]["data"]["multiple_files"][0]
            ).json()

            self.assertEqual(
                attachment_1["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7",
            )
            self.assertEqual(
                attachment_2_1["informatieobjecttype"],
                "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/"
                "531f6c1a-97f7-478c-85f0-67d2f23661c7",
            )

    def test_mapping_file_components_container_variable(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "key": "single_file",
                    "label": "single_file",
                    "file": {"type": []},
                    "filePattern": "",
                },
                {
                    "type": "file",
                    "key": "multiple_files",
                    "label": "multiple_files",
                    "file": {"type": []},
                    "filePattern": "",
                    "multiple": True,
                },
            ],
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 3, 19, 13, 40, 34).replace(tzinfo=UTC),
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
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "catalogue": {"domain": "TEST", "rsin": "000000000"},
            "iot_attachment": "Attachment Informatieobjecttype",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                {
                    "variable_key": "attachment_urls",
                    "target_path": ["multiple_files"],
                },
            ],
            "transform_to_list": [],
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        assert result is not None
        self.assertIsInstance(result["record"]["data"]["multiple_files"], list)
        self.assertEqual(len(result["record"]["data"]["multiple_files"]), 2)

    @tag("gh-4689")
    def test_submission_with_editgrid_with_nested_files(self):
        formio_upload = SubmittedFileFactory.build()
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "repeatingGroup",
                    "type": "editgrid",
                    "label": "Repeating group",
                    "groupLabel": "Item",
                    "components": [
                        {
                            "key": "nestedRepeatingGroup",
                            "type": "editgrid",
                            "label": "Yeah this is madness",
                            "groupLabel": "Item",
                            "components": [
                                {
                                    "key": "email",
                                    "type": "email",
                                    "label": "Email",
                                },
                                {
                                    "type": "file",
                                    "key": "file",
                                    "label": "file",
                                    "file": {"type": []},
                                    "filePattern": "",
                                    "multiple": False,
                                },
                            ],
                        }
                    ],
                },
            ],
            submitted_data={
                "repeatingGroup": [
                    {
                        "nestedRepeatingGroup": [
                            {
                                "email": "info@example.com",
                                "file": formio_upload,
                            }
                        ],
                    },
                ],
            },
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 3, 19, 13, 40, 34).replace(tzinfo=UTC),
        )
        submission_step = submission.steps[0]
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            submission_variable__key="repeatingGroup",
            file_name=formio_upload["originalName"],
            original_name=formio_upload["originalName"],
            _component_configuration_path="components.0.components.0.components.1",
            _component_data_path="repeatingGroup.0.nestedRepeatingGroup.0.file",
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "catalogue": {"domain": "TEST", "rsin": "000000000"},
            "iot_attachment": "Attachment Informatieobjecttype",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                {
                    "variable_key": "repeatingGroup",
                    "target_path": ["repeatingGroup"],
                },
            ],
            "transform_to_list": [],
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        assert result is not None
        objects_api_attachment = attachment.objectsapisubmissionattachment_set.get()
        record_data = result["record"]["data"]
        expected = {
            "repeatingGroup": [
                {
                    "nestedRepeatingGroup": [
                        {
                            "email": "info@example.com",
                            "file": objects_api_attachment.document_url,
                        }
                    ],
                }
            ],
        }
        self.assertEqual(record_data, expected)

    def test_submission_with_empty_optional_file(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "key": "single_file",
                    "label": "single_file",
                    "file": {"type": []},
                    "filePattern": "",
                },
            ],
            submitted_data={"single_file": []},
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 3, 19, 13, 40, 34).replace(tzinfo=UTC),
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "catalogue": {"domain": "TEST", "rsin": "000000000"},
            "iot_attachment": "Attachment Informatieobjecttype",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                {
                    "variable_key": "single_file",
                    "target_path": ["single_file"],
                },
            ],
            "transform_to_list": [],
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        assert result is not None

    def test_can_upload_attachments_with_file_component_specific_overrides(self):
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "key": "file",
                    "label": "File",
                    "file": {"type": []},
                    "filePattern": "",
                    "registration": {
                        "informatieobjecttype": "https://example.com/ignore-me",
                    },
                }
            ],
            submitted_data={},
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 7, 1, 12, 0, 0).replace(tzinfo=UTC),
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission.steps[0],
            content_type="image/png",
            submission_variable__key="file",
            _component_configuration_path="components.0",
        )
        options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "environment",
                    "target_path": ["environment"],
                },
            ],
            "transform_to_list": [],
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            # a default is required to register file component attachments
            "iot_attachment": "PDF Informatieobjecttype",
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "upload_submission_csv": False,
            "files": [
                {
                    "key": "file",
                    "document_type_description": "Attachment Informatieobjecttype",
                    "title": "Custom title",
                },
            ],
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, options)

        assert result is not None
        with get_documents_client(objects_api_group) as documents_client:
            attachment_document = documents_client.get(
                ObjectsAPISubmissionAttachment.objects.get(
                    submission_file_attachment=attachment
                ).document_url
            ).json()

        self.assertEqual(
            attachment_document["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
        )
        self.assertEqual(attachment_document["titel"], "Custom title")

    def test_addressNl_legacy_before_of_30(self):
        """
        Test the behaviour on the previous iteration of addressNL mapping configuration.

        Before Open Forms 3.0 you could only map the entiry addressNL component to a
        single target path. Since 3.0, additional mapping options are available. This
        test ensures that legacy configured registration backends still work without
        extra modifications, albeit the behaviour may be changed.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "addressNl",
                    "type": "addressNL",
                    "label": "AddressNl component",
                },
            ],
            submitted_data={
                "addressNl": {
                    "city": "",
                    "postcode": "1025 xm",
                    "streetName": "",
                    "houseLetter": "d",
                    "houseNumber": "73",
                    "secretStreetCity": "",
                    "houseNumberAddition": "2",
                },
            },
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 3, 19, 13, 40, 34).replace(tzinfo=UTC),
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        # simulates old, non-migrated options structure
        serializer = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "8faed0fa-7864-4409-aa6d-533a37616a9e",
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
                "variables_mapping": [
                    {
                        "variable_key": "addressNl",
                        "target_path": ["destinationAddressNL"],
                    },
                ],
            }
        )
        is_valid = serializer.is_valid()
        assert is_valid
        v2_options: RegistrationOptionsV2 = serializer.validated_data
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "destinationAddressNL": {
                    "city": "",
                    "postcode": "1025 xm",
                    "streetName": "",
                    "houseLetter": "d",
                    "houseNumber": "73",
                    "houseNumberAddition": "2",
                }
            },
        )

    @tag("gh-5034")
    def test_object_ownership_not_validated_if_new_object(self):
        submission = SubmissionFactory.from_components(
            [{"key": "textfield", "type": "textfield"}],
            submitted_data={"textfield": "test"},
            completed_not_preregistered=True,
            form__registration_backend=PLUGIN_IDENTIFIER,
            form__registration_backend_options={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "8faed0fa-7864-4409-aa6d-533a37616a9e",
                "objecttype_version": 1,
                "update_existing_object": False,
                "auth_attribute_path": [],
                "variables_mapping": [],
            },
            initial_data_reference="some ref",
        )

        try:
            pre_registration(submission.pk, PostSubmissionEvents.on_retry)
        except AssertionError:
            self.fail("Assertion should have passed.")

    @tag("gh-6007")
    def test_hidden_fields_still_get_emitted_to_object(self):
        """
        Assert that components that are hidden are not omitted from the JSON payload.

        4a295cb968ed8f96dee7d27405c9cb4a80defd19 results in hidden fields no longer
        creating a database record for the hidden variable, but it *is* still available
        in the submission state and should be processed accordingly.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "textfield",
                    "label": "textfield",
                    "hidden": True,
                },
                {
                    "type": "fieldset",
                    "key": "hiddenFieldset",
                    "label": "hiddenFieldset",
                    "hidden": True,
                    "components": [
                        {
                            "type": "textfield",
                            "key": "nestedTextfield",
                            "label": "nestedTextfield",
                            "hidden": False,
                        }
                    ],
                },
            ],
            submitted_data={},
            completed=True,
        )
        state = submission.variables_state
        assert not state.saved_variables
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "textfield",
                    "target_path": ["textfield"],
                },
                {
                    "variable_key": "nestedTextfield",
                    "target_path": ["nestedTextfield"],
                },
            ],
            "transform_to_list": [],
            "catalogue": {"rsin": "", "domain": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        assert result is not None
        self.assertEqual(
            result["record"]["data"],
            {
                "textfield": "",
                "nestedTextfield": "",
            },
        )

    @tag("dh-864")
    def test_conditional_fieldset_inside_repeating_group(self):
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            organisatie_rsin="000000000",
        )
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "checkbox",
                    "key": "showNestedFieldset",
                    "label": "Show nested fieldset",
                },
                {
                    "type": "editgrid",
                    "key": "repeatingGroup",
                    "label": "Repeating group",
                    "groupLabel": "Item",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "editgridTextfield",
                            "label": "Edit grid text field",
                        },
                        {
                            "type": "fieldset",
                            "key": "editgridFieldset",
                            "label": "Edit grid fieldset",
                            "conditional": {
                                "show": True,
                                "when": "showNestedFieldset",
                                "eq": True,
                            },
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "container.nestedTextfield",
                                    "label": "Nested text field",
                                },
                            ],
                        },
                    ],
                },
            ],
            submitted_data={
                # leads to no submission data for the fields inside the fieldset,
                # because they aren't visible
                "showNestedFieldset": False,
                "repeatingGroup": [
                    {
                        "editgridTextfield": "foo",
                    }
                ],
            },
            completed=True,
            # the version of the document types are valid on this timestamp
            completed_on=datetime(2024, 7, 1, 12, 0, 0).replace(tzinfo=UTC),
        )
        options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "update_existing_object": False,
            "auth_attribute_path": [],
            "variables_mapping": [
                {
                    "variable_key": "showNestedFieldset",
                    "target_path": ["fieldsetShown"],
                },
                {
                    "variable_key": "repeatingGroup",
                    "target_path": ["repeatingGroupItems"],
                },
            ],
            "transform_to_list": [],
            "upload_submission_csv": False,
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, options)

        assert result is not None
        record_data = result["record"]["data"]
        self.assertEqual(
            record_data,
            {
                "fieldsetShown": False,
                "repeatingGroupItems": [
                    {
                        "editgridTextfield": "foo",
                        # the component key structure is used in the output of the mapped
                        # item of the edit grid.
                        # Note that DH would expect this parent key and child not to be
                        # present at all, however because of #6007 we can't do that,
                        # unless #6012 gets implemented.
                        "container": {
                            "nestedTextfield": "",
                        },
                    },
                ],
            },
        )


@temp_private_root()
class FamilyMembersRegistrationTests(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        ),
    )
    @patch(
        "openforms.config.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        ),
    )
    def test_submission_with_partners_component(self, m, n):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "partners",
                    "type": "partners",
                    "registration": {
                        "attribute": RegistrationAttribute.partners,
                    },
                }
            ],
            auth_info__value="000009921",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
        )
        FormVariableFactory.create(
            key="partners_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
                "min_age": None,
                "max_age": None,
            },
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("59cdc902-576b-495f-ae63-c9c78b8afc09"),
            "objecttype_version": 1,
            "upload_submission_csv": False,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "auth_attribute_path": [],
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "partners",
                    "target_path": ["partners"],
                },
            ],
            "transform_to_list": [],
        }
        prefill_variables(submission)
        handler = ObjectsAPIV2Handler()
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "partners": [
                    {
                        "bsn": "999995182",
                        "initials": "A.M.P.",
                        "affixes": "",
                        "lastName": "Jansma",
                        "firstNames": "Anna Maria Petra",
                        "dateOfBirth": "1945-04-18",
                    },
                    {
                        "bsn": "123456782",
                        "initials": "T.s.p.",
                        "affixes": "",
                        "lastName": "Test",
                        "firstNames": "Test second partner",
                        "dateOfBirth": "1945-04-18",
                    },
                ]
            },
        )

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        ),
    )
    @patch(
        "openforms.config.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        ),
    )
    def test_submission_with_children_component_and_selection_disabled(self, m, n):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "children",
                    "key": "children",
                    "label": "children",
                    "enableSelection": False,
                }
            ],
            auth_info__value="999970094",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("db4e8653-1f84-4df7-82bd-96787c52b298"),
            "objecttype_version": 1,
            "upload_submission_csv": False,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "auth_attribute_path": [],
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "children",
                    "target_path": ["children"],
                },
            ],
            "transform_to_list": [],
        }
        prefill_variables(submission)
        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        state = submission.variables_state
        children_data = state.get_data()["children"]
        assert isinstance(children_data, list)
        for child in children_data:
            assert isinstance(child, dict)
            child.update(
                {
                    "selected": None,
                    "__id": str(uuid4()),
                    "__addedManually": False,
                }
            )
        handler = ObjectsAPIV2Handler()
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "children": [
                    {
                        "bsn": "999970100",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Olle",
                        "dateOfBirth": "2022-02-02",
                    },
                    {
                        "bsn": "999970112",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Onne",
                        "dateOfBirth": "2022-02-02",
                    },
                ],
            },
        )

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/",
                auth_type=AuthTypes.no_auth,
            ),
            brp_personen_version=BRPVersions.v20,
        ),
    )
    @patch(
        "openforms.config.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        ),
    )
    def test_submission_with_children_component_and_selection_enabled(self, m, n):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "children",
                    "key": "children",
                    "label": "children",
                    "enableSelection": True,
                }
            ],
            auth_info__value="999970094",
            auth_info__attribute=AuthAttribute.bsn,
            completed_on=datetime(2024, 11, 9, 15, 30, 0).replace(tzinfo=UTC),
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=submission.form,
            user_defined=True,
            prefill_plugin=FM_PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("db4e8653-1f84-4df7-82bd-96787c52b298"),
            "objecttype_version": 1,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "auth_attribute_path": [],
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "children",
                    "target_path": ["children"],
                },
            ],
            "transform_to_list": [],
        }
        prefill_variables(submission)
        # the submitted data needs extra handling because frontend adds some extra field
        # to it which is not happenning here, so we have to update it manually in order
        # to mimic the frontend behaviour
        state = submission.variables_state
        children_data = state.get_data()["children"]
        assert isinstance(children_data, list)
        assert isinstance(children_data[0], dict)
        assert isinstance(children_data[1], dict)
        children_data[0].update(
            {
                "selected": True,
                "__id": str(uuid4()),
                "__addedManually": False,
            }
        )
        children_data[1].update(
            {
                "selected": False,
                "__id": str(uuid4()),
                "__addedManually": False,
            }
        )
        handler = ObjectsAPIV2Handler()
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "children": [
                    {
                        "bsn": "999970100",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Olle",
                        "dateOfBirth": "2022-02-02",
                    },
                ],
            },
        )

    def test_submission_with_children_component_added_manually_and_selection_enabled(
        self,
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "children",
                    "key": "children",
                    "label": "children",
                    "enableSelection": True,
                },
            ],
            submitted_data={
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
            bsn="123456782",
            completed=True,
            with_public_registration_reference=True,
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("db4e8653-1f84-4df7-82bd-96787c52b298"),
            "objecttype_version": 1,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "auth_attribute_path": [],
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "children",
                    "target_path": ["children"],
                },
            ],
            "transform_to_list": [],
        }
        handler = ObjectsAPIV2Handler()
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "children": [
                    {
                        "bsn": "999970100",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Olle",
                        "dateOfBirth": "2022-02-02",
                    },
                ],
            },
        )

    def test_submission_with_children_component_added_manually_and_selection_disabled(
        self,
    ):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "children",
                    "key": "children",
                    "label": "children",
                    "enableSelection": False,
                },
            ],
            submitted_data={
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
            bsn="123456782",
            completed=True,
            with_public_registration_reference=True,
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("db4e8653-1f84-4df7-82bd-96787c52b298"),
            "objecttype_version": 1,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "auth_attribute_path": [],
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "children",
                    "target_path": ["children"],
                },
            ],
            "transform_to_list": [],
        }
        handler = ObjectsAPIV2Handler()
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "children": [
                    {
                        "bsn": "999970100",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Olle",
                        "dateOfBirth": "2022-02-02",
                    },
                    {
                        "bsn": "999970112",
                        "affixes": "",
                        "initials": "O.",
                        "lastName": "Oostingh",
                        "firstNames": "Onne",
                        "dateOfBirth": "2022-02-02",
                    },
                ],
            },
        )

    def test_submission_with_children_component_two_steps_and_selection_disabled(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "children",
                    "key": "children",
                    "label": "children",
                    "enableSelection": False,
                },
                {
                    "type": "editgrid",
                    "key": "extraChildDetails",
                    "label": "extraChildDetails",
                    "groupLabel": "Item",
                    "components": [
                        {
                            "type": "bsn",
                            "key": "bsn",
                            "label": "bsn",
                        },
                        {
                            "type": "textfield",
                            "key": "firstNames",
                            "label": "Child name",
                        },
                    ],
                },
            ],
            submitted_data={
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
                        "selected": None,
                        "__addedManually": False,
                        "__id": str(uuid4()),
                    },
                ],
                "extraChildDetails": [
                    {"bsn": "999970100", "firstNames": "Olle"},
                    {"bsn": "999970112", "firstNames": "Onne"},
                ],
            },
            bsn="999970094",
            completed=True,
            with_public_registration_reference=True,
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("db4e8653-1f84-4df7-82bd-96787c52b298"),
            "objecttype_version": 1,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "auth_attribute_path": [],
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "children",
                    "target_path": ["children"],
                },
                {
                    "variable_key": "extraChildDetails",
                    "target_path": ["extraChildDetails"],
                },
            ],
            "transform_to_list": [],
        }
        handler = ObjectsAPIV2Handler()
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "children": [
                    {
                        "affixes": "",
                        "bsn": "999970100",
                        "dateOfBirth": "2022-02-02",
                        "firstNames": "Olle",
                        "initials": "O.",
                        "lastName": "Oostingh",
                    },
                    {
                        "affixes": "",
                        "bsn": "999970112",
                        "dateOfBirth": "2022-02-02",
                        "firstNames": "Onne",
                        "initials": "O.",
                        "lastName": "Oostingh",
                    },
                ],
                "extraChildDetails": [
                    {"bsn": "999970100", "firstNames": "Olle"},
                    {"bsn": "999970112", "firstNames": "Onne"},
                ],
            },
        )

    def test_submission_with_children_component_two_steps_and_selection_enabled(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "children",
                    "key": "children",
                    "label": "children",
                    "enableSelection": True,
                },
                {
                    "type": "editgrid",
                    "key": "extraChildDetails",
                    "label": "extraChildDetails",
                    "groupLabel": "Item",
                    "components": [
                        {
                            "type": "bsn",
                            "key": "bsn",
                            "label": "bsn",
                        },
                        {
                            "type": "textfield",
                            "key": "firstNames",
                            "label": "Child name",
                        },
                    ],
                },
            ],
            submitted_data={
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
                "extraChildDetails": [
                    {"bsn": "999970100", "firstNames": "Olle"},
                ],
            },
            bsn="999970094",
            completed=True,
            with_public_registration_reference=True,
        )

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("db4e8653-1f84-4df7-82bd-96787c52b298"),
            "objecttype_version": 1,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
            "upload_submission_csv": False,
            "auth_attribute_path": [],
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "children",
                    "target_path": ["children"],
                },
                {
                    "variable_key": "extraChildDetails",
                    "target_path": ["extraChildDetails"],
                },
            ],
            "transform_to_list": [],
        }
        handler = ObjectsAPIV2Handler()
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data,
            {
                "children": [
                    {
                        "affixes": "",
                        "bsn": "999970100",
                        "dateOfBirth": "2022-02-02",
                        "firstNames": "Olle",
                        "initials": "O.",
                        "lastName": "Oostingh",
                    },
                ],
                "extraChildDetails": [
                    {"bsn": "999970100", "firstNames": "Olle"},
                ],
            },
        )
