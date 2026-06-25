from uuid import UUID

from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time

from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ObjectsAPIRegistrationData
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from ..typing import RegistrationOptionsV2


@freeze_time("2020-02-02")
class ObjectsAPIPaymentStatusUpdateV2Tests(OFVCRMixin, TestCase):
    config_group: ObjectsAPIGroupConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
        )

    def test_update_payment_status(self):
        # We manually create the objects instance, to be in the same state after
        # `plugin.register_submission` was called:
        with get_objects_client(self.config_group) as client:
            data = client.create_object(
                record_data=prepare_data_for_registration(
                    data={
                        "age": 20,
                        "name": {
                            "last.name": "My last name",
                        },
                        "submission_pdf_url": "http://example.com",
                        "submission_csv_url": "http://example.com",
                        "submission_payment_completed": False,
                        "nested": {
                            "unrelated": "some_value",
                            "submission_payment_amount": 0,
                        },
                        "submission_payment_public_ids": [],
                        "submission_date": timezone.now().isoformat(),
                    },
                    objecttype_version=3,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )
            # Because of the nginx reverse proxy, we need to set the correct
            # host as this URL will be used by the plugin to update the payment status:
            objects_url = data["url"].replace("objects-web:8000", "localhost:8002")

        submission = SubmissionFactory.from_components(
            [
                {"key": "age", "type": "number"},
                {"key": "lastname", "type": "textfield"},
                {"key": "location", "type": "map"},
            ],
            registration_success=True,
            submitted_data={
                "age": 20,
                "lastname": "My last name",
                "location": {
                    "type": "Point",
                    "coordinates": [4.893164274470299, 52.36673378967122],
                },
            },
            registration_result={"url": objects_url},
            form__payment_backend="demo",
            form__product__price=10.01,
        )
        SubmissionPaymentFactory.create(
            submission=submission,
            status=PaymentStatus.completed,
            amount=10.01,
            public_order_id="TEST-123",
            provider_payment_id="12345",
        )
        ObjectsAPIRegistrationData.objects.create(submission=submission)
        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.config_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "catalogue": {"domain": "", "rsin": ""},
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "auth_attribute_path": [],
            "update_existing_object": False,
            "upload_submission_csv": True,
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
                    "target_path": ["nested", "submission_payment_amount"],
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
            "geometry_variable_key": "location",
            "transform_to_list": [],
        }
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        result = plugin.update_payment_status(submission, v2_options)

        assert result is not None
        result_data = result["record"]["data"]
        self.assertTrue(result_data["submission_payment_completed"])
        self.assertEqual(
            result_data["nested"],
            {
                "unrelated": "some_value",
                "submission_payment_amount": 10.01,
            },
        )
        self.assertEqual(result_data["submission_payment_public_ids"], ["TEST-123"])
        self.assertEqual(result_data["submission_provider_payment_ids"], ["12345"])
