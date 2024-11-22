from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase, tag
from django.utils import timezone

from freezegun import freeze_time

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionValueVariableFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ObjectsAPIConfig, ObjectsAPIRegistrationData
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from ..registration_variables import PaymentAmount
from ..submission_registration import ObjectsAPIV2Handler
from ..typing import RegistrationOptionsV2

VCR_TEST_FILES = Path(__file__).parent / "files"


@freeze_time("2024-03-19T13:40:34.222258+00:00")
class ObjectsAPIBackendV2Tests(OFVCRMixin, TestCase):
    """This test case requires the Objects & Objecttypes API and Open Zaak to be running.

    See the relevant Docker compose in the ``docker/`` folder.
    """

    maxDiff = None
    VCR_TEST_FILES = VCR_TEST_FILES

    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=ObjectsAPIConfig(),
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def test_submission_with_objects_api_v2(self):
        submission = SubmissionFactory.from_components(
            [
                # fmt: off
                {
                    "key": "age",
                    "type": "number"
                },
                {
                    "key": "lastname",
                    "type": "textfield",
                },
                {
                    "key": "location",
                    "type": "map",
                },
                # fmt: on
            ],
            completed=True,
            submitted_data={
                "age": 20,
                "lastname": "My last name",
                "location": [52.36673378967122, 4.893164274470299],
            },
        )

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": True,
            "update_existing_object": False,
            "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
            "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
            "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                # fmt: off
                {
                    "variable_key": "age",
                    "target_path": ["age"],
                },
                {
                    "variable_key": "lastname",
                    "target_path": ["name", "last.name"]
                },
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
                # fmt: on
            ],
            "geometry_variable_key": "location",
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        registration_data = ObjectsAPIRegistrationData.objects.get(
            submission=submission
        )

        self.assertEqual(
            result["type"],
            "http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
        )
        self.assertEqual(
            result["record"]["typeVersion"], v2_options["objecttype_version"]
        )
        submission_date = timezone.now().replace(second=0, microsecond=0).isoformat()
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
                "coordinates": [52.36673378967122, 4.893164274470299],
            },
        )

    def test_submission_with_objects_api_v2_with_payment_attributes(self):
        submission = SubmissionFactory.from_components(
            [],
            completed=True,
            submitted_data={},
        )

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "upload_submission_csv": False,
            "update_existing_object": False,
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

        self.assertEqual(
            result["type"],
            "http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
        )
        self.assertEqual(result["record"]["typeVersion"], 3)

        data = result["record"]["data"]

        self.assertEqual(data["submission_payment_completed"], True)
        self.assertEqual(data["submission_payment_amount"], 40.0)
        self.assertEqual(data["submission_payment_public_ids"], ["foo", "bar"])
        self.assertEqual(data["submission_provider_payment_ids"], ["123456", "654321"])

    def test_submission_with_file_components(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "single_file",
                    "type": "file",
                },
                {
                    "key": "multiple_files",
                    "type": "file",
                    "multiple": True,
                },
            ],
            completed=True,
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment1.jpg",
            form_key="single_file",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment2_1.jpg",
            form_key="multiple_files",
        )

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "upload_submission_csv": False,
            "update_existing_object": False,
            "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                # fmt: off
                {
                    "variable_key": "single_file",
                    "target_path": ["single_file"],
                },
                {
                    "variable_key": "multiple_files",
                    "target_path": ["multiple_files"]
                },
                # fmt: on
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        self.assertEqual(
            result["type"],
            "http://objecttypes-web:8000/api/v2/objecttypes/527b8408-7421-4808-a744-43ccb7bdaaa2",
        )
        self.assertEqual(
            result["record"]["typeVersion"], v2_options["objecttype_version"]
        )

        self.assertTrue(
            result["record"]["data"]["single_file"].startswith(
                "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/"
            )
        )

        self.assertIsInstance(result["record"]["data"]["multiple_files"], list)
        self.assertEqual(len(result["record"]["data"]["multiple_files"]), 1)

    def test_submission_with_file_components_container_variable(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "single_file",
                    "type": "file",
                },
                {
                    "key": "multiple_files",
                    "type": "file",
                    "multiple": True,
                },
            ],
            completed=True,
        )
        submission_step = submission.steps[0]
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment1.jpg",
            form_key="single_file",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=submission_step,
            file_name="attachment2_1.jpg",
            form_key="multiple_files",
        )

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "upload_submission_csv": False,
            "update_existing_object": False,
            "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                {
                    "variable_key": "attachment_urls",
                    "target_path": ["multiple_files"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)
        assert result is not None

        self.assertIsInstance(result["record"]["data"]["multiple_files"], list)
        self.assertEqual(len(result["record"]["data"]["multiple_files"]), 2)

    def test_submission_with_empty_optional_file(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "single_file",
                    "type": "file",
                },
            ],
            completed=True,
        )
        SubmissionValueVariableFactory.create(
            submission=submission,
            form_variable=submission.form.formvariable_set.get(key="single_file"),
            key="single_file",
            value=[],
        )
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("527b8408-7421-4808-a744-43ccb7bdaaa2"),
            "objecttype_version": 1,
            "upload_submission_csv": False,
            "update_existing_object": False,
            "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            "organisatie_rsin": "000000000",
            "variables_mapping": [
                # fmt: off
                {
                    "variable_key": "single_file",
                    "target_path": ["single_file"],
                },
                # fmt: on
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        # Run the registration
        result = plugin.register_submission(submission, v2_options)

        assert result is not None


class V2HandlerTests(TestCase):
    """
    Test V2 registration backend without actual HTTP calls.

    Test the behaviour of the V2 registration handler for producing record data to send
    to the Objects API.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.group = ObjectsAPIGroupConfigFactory(
            objecttypes_service__api_root="https://objecttypen.nl/api/v2/",
        )

    def test_submission_with_map_component_inside_data(self):
        """
        A map component can be explicitly mapped to an attribute inside the 'data' key.

        This happens when more than one map component is in the form, and only one can
        be mapped to the ``record.geometry`` path, the rest must go in ``record.data.``.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "location",
                    "type": "map",
                    "label": "Map with point coordinate",
                },
            ],
            completed=True,
            submitted_data={
                "location": [52.36673378967122, 4.893164274470299],
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "location",
                    "target_path": ["pointCoordinates"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        self.assertEqual(
            data["pointCoordinates"],
            {
                "type": "Point",
                "coordinates": [52.36673378967122, 4.893164274470299],
            },
        )

    @tag("gh-4141")
    def test_layout_components(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "fieldset",
                    "type": "fieldset",
                    "components": [{"key": "fieldset.textfield", "type": "textfield"}],
                },
            ],
            completed=True,
            submitted_data={
                "fieldset": {
                    "textfield": "some_string",
                },
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "fieldset.textfield",
                    "target_path": ["textfield"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(data["textfield"], "some_string")

    @tag("gh-4202")
    def test_hidden_component(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "textfield",
                    "type": "textfield",
                },
                {
                    "key": "hidden_number",
                    "type": "number",
                    "hidden": True,
                },
            ],
            completed=True,
            submitted_data={
                "textfield": "some_string",
            },
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "textfield",
                    "target_path": ["textfield"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(data["textfield"], "some_string")

    def test_public_reference_available(self):
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            public_registration_reference="OF-911",
            auth_info__plugin="irrelevant",
            auth_info__is_eh_bewindvoering=True,
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "public_reference",
                    "target_path": ["of_nummer"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        self.assertEqual(record_data["data"], {"of_nummer": "OF-911"})

    def test_cosign_info_available(self):
        now = timezone.now().isoformat()

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "validate": {"required": False},
                },
            ],
            completed=True,
            submitted_data={
                "cosign": "example@localhost",
            },
            cosign_complete=True,
            co_sign_data={
                "value": "123456789",
                "attribute": AuthAttribute.bsn,
                "cosign_date": now,
            },
        )

        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "cosign_data",
                    "target_path": ["cosign_data"],
                },
                {
                    "variable_key": "cosign_date",
                    "target_path": ["cosign_date"],
                },
                {
                    "variable_key": "cosign_bsn",
                    "target_path": ["cosign_bsn"],
                },
                {
                    "variable_key": "cosign_kvk",  # Will be empty string as bsn was used.
                    "target_path": ["cosign_kvk"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(
            data["cosign_data"],
            {
                "value": "123456789",
                "attribute": AuthAttribute.bsn,
                "cosign_date": now,
            },
        )
        self.assertEqual(data["cosign_date"], now)
        self.assertEqual(data["cosign_bsn"], "123456789")
        self.assertEqual(data["cosign_kvk"], "")

    def test_cosign_info_not_available(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "validate": {"required": False},
                },
            ],
            completed=True,
            submitted_data={
                "cosign": "example@localhost",
            },
            cosign_complete=False,
        )

        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "cosign_date",
                    "target_path": ["cosign_date"],
                },
                {
                    "variable_key": "cosign_bsn",
                    "target_path": ["cosign_bsn"],
                },
                {
                    "variable_key": "cosign_pseudo",  # Will be empty string as bsn was used.
                    "target_path": ["cosign_pseudo"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(data["cosign_date"], None)
        self.assertEqual(data["cosign_pseudo"], "")

    def test_cosign_info_no_cosign_date(self):
        """The cosign date might not be available on existing submissions."""

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "cosign",
                    "type": "cosign",
                    "validate": {"required": False},
                },
            ],
            completed=True,
            submitted_data={
                "cosign": "example@localhost",
            },
            cosign_complete=True,
            co_sign_data={
                "value": "123456789",
                "attribute": AuthAttribute.bsn,
            },
        )

        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "cosign_date",
                    "target_path": ["cosign_date"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        record_data = handler.get_record_data(submission=submission, options=v2_options)
        data = record_data["data"]

        self.assertEqual(data["cosign_date"], None)

    @tag("utrecht-243", "gh-4425")
    def test_payment_variable_without_any_payment_attempts(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__payment_backend="demo",
            form__product__price=10,
        )
        assert not submission.payments.exists()
        assert submission.price == 10
        variable = PaymentAmount("dummy")

        value = variable.get_initial_value(submission=submission)

        self.assertEqual(value, 10.0)

    def test_auth_context_data_info_available(self):
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "auth_context",
                    "target_path": ["auth_context"],
                },
                {
                    "variable_key": "auth_context_source",
                    "target_path": ["authn", "middel"],
                },
                {
                    "variable_key": "auth_context_loa",
                    "target_path": ["authn", "loa"],
                },
                {
                    "variable_key": "auth_context_representee_identifier",
                    "target_path": ["authn", "vertegenwoordigde"],
                },
                {
                    "variable_key": "auth_context_representee_identifier_type",
                    "target_path": ["authn", "soort_vertegenwoordigde"],
                },
                {
                    "variable_key": "auth_context_legal_subject_identifier",
                    "target_path": ["authn", "gemachtigde"],
                },
                {
                    "variable_key": "auth_context_legal_subject_identifier_type",
                    "target_path": ["authn", "soort_gemachtigde"],
                },
                {
                    "variable_key": "auth_context_acting_subject_identifier",
                    "target_path": ["authn", "actor"],
                },
                {
                    "variable_key": "auth_context_acting_subject_identifier_type",
                    "target_path": ["authn", "soort_actor"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            auth_info__plugin="irrelevant",
            auth_info__is_eh_bewindvoering=True,
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)

        record_data = handler.get_record_data(submission=submission, options=v2_options)

        data = record_data["data"]
        with self.subTest("full auth context"):
            expected_auth_context = {
                "source": "eherkenning",
                "levelOfAssurance": "urn:etoegang:core:assurance-class:loa3",
                "representee": {
                    "identifierType": "bsn",
                    "identifier": "999991607",
                },
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "kvkNummer",
                        "identifier": "90002768",
                    },
                    "actingSubject": {
                        "identifierType": "opaque",
                        "identifier": (
                            "4B75A0EA107B3D36C82FD675B5B78CC2F"
                            "181B22E33D85F2D4A5DA63452EE3018@2"
                            "D8FF1EF10279BC2643F376D89835151"
                        ),
                    },
                },
                "mandate": {
                    "role": "bewindvoerder",
                    "services": [
                        {
                            "id": "urn:etoegang:DV:00000001002308836000:services:9113",
                            "uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                        }
                    ],
                },
            }
            self.assertEqual(data["auth_context"], expected_auth_context)

        with self.subTest("individual auth context vars"):
            expected_obj = {
                "middel": "eherkenning",
                "loa": "urn:etoegang:core:assurance-class:loa3",
                "vertegenwoordigde": "999991607",
                "soort_vertegenwoordigde": "bsn",
                "gemachtigde": "90002768",
                "soort_gemachtigde": "kvkNummer",
                "actor": (
                    "4B75A0EA107B3D36C82FD675B5B78CC2F"
                    "181B22E33D85F2D4A5DA63452EE3018@2"
                    "D8FF1EF10279BC2643F376D89835151"
                ),
                "soort_actor": "opaque",
            }
            self.assertEqual(data["authn"], expected_obj)

    def test_auth_context_data_info_parts_missing_variants(self):
        v2_options: RegistrationOptionsV2 = {
            "objects_api_group": self.group,
            "version": 2,
            "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "variables_mapping": [
                {
                    "variable_key": "auth_context",
                    "target_path": ["auth_context"],
                },
                {
                    "variable_key": "auth_context_source",
                    "target_path": ["authn", "middel"],
                },
                {
                    "variable_key": "auth_context_loa",
                    "target_path": ["authn", "loa"],
                },
                {
                    "variable_key": "auth_context_representee_identifier",
                    "target_path": ["authn", "vertegenwoordigde"],
                },
                {
                    "variable_key": "auth_context_representee_identifier_type",
                    "target_path": ["authn", "soort_vertegenwoordigde"],
                },
                {
                    "variable_key": "auth_context_legal_subject_identifier",
                    "target_path": ["authn", "gemachtigde"],
                },
                {
                    "variable_key": "auth_context_legal_subject_identifier_type",
                    "target_path": ["authn", "soort_gemachtigde"],
                },
                {
                    "variable_key": "auth_context_acting_subject_identifier",
                    "target_path": ["authn", "actor"],
                },
                {
                    "variable_key": "auth_context_acting_subject_identifier_type",
                    "target_path": ["authn", "soort_actor"],
                },
            ],
            "iot_attachment": "",
            "iot_submission_csv": "",
            "iot_submission_report": "",
        }
        handler = ObjectsAPIV2Handler()

        cases = [
            (
                "anonymous",
                SubmissionFactory.create(
                    with_public_registration_reference=True,
                    auth_info=None,
                ),
                {
                    "middel": "",
                    "loa": "",
                    "vertegenwoordigde": "",
                    "soort_vertegenwoordigde": "",
                    "gemachtigde": "",
                    "soort_gemachtigde": "",
                    "actor": "",
                    "soort_actor": "",
                },
            ),
            (
                "digid",
                SubmissionFactory.create(
                    with_public_registration_reference=True,
                    auth_info__is_digid=True,
                ),
                {
                    "middel": "digid",
                    "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                    "vertegenwoordigde": "",
                    "soort_vertegenwoordigde": "",
                    "gemachtigde": "999991607",
                    "soort_gemachtigde": "bsn",
                    "actor": "",
                    "soort_actor": "",
                },
            ),
            (
                "digid-machtigen",
                SubmissionFactory.create(
                    with_public_registration_reference=True,
                    auth_info__is_digid_machtigen=True,
                ),
                {
                    "middel": "digid",
                    "loa": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                    "vertegenwoordigde": "999991607",
                    "soort_vertegenwoordigde": "bsn",
                    "gemachtigde": "999999999",
                    "soort_gemachtigde": "bsn",
                    "actor": "",
                    "soort_actor": "",
                },
            ),
            (
                "eherkenning",
                SubmissionFactory.create(
                    with_public_registration_reference=True,
                    auth_info__is_eh=True,
                ),
                {
                    "middel": "eherkenning",
                    "loa": "urn:etoegang:core:assurance-class:loa3",
                    "vertegenwoordigde": "",
                    "soort_vertegenwoordigde": "",
                    "gemachtigde": "90002768",
                    "soort_gemachtigde": "kvkNummer",
                    "actor": (
                        "4B75A0EA107B3D36C82FD675B5B78CC2F"
                        "181B22E33D85F2D4A5DA63452EE3018@2"
                        "D8FF1EF10279BC2643F376D89835151"
                    ),
                    "soort_actor": "opaque",
                },
            ),
        ]

        for label, submission, expected in cases:
            with self.subTest(labe=label):
                ObjectsAPIRegistrationData.objects.create(submission=submission)

                record_data = handler.get_record_data(
                    submission=submission, options=v2_options
                )

                data = record_data["data"]
                self.assertEqual(data["authn"], expected)
