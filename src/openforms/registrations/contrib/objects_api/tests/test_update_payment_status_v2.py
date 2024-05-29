from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..client import get_objects_client
from ..models import ObjectsAPIConfig, ObjectsAPIGroupConfig, ObjectsAPIRegistrationData
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from ..typing import RegistrationOptionsV2


@freeze_time("2020-02-02")
class ObjectsAPIPaymentStatusUpdateV2Tests(OFVCRMixin, TestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self):
        super().setUp()

        self.config_group = ObjectsAPIGroupConfig(
            objects_service=ServiceFactory.build(
                api_root="http://localhost:8002/api/v2/",
                api_type=APITypes.orc,
                oas="https://example.com/",
                header_key="Authorization",
                # See the docker compose fixtures:
                header_value="Token 7657474c3d75f56ae0abd0d1bf7994b09964dca9",
                auth_type=AuthTypes.api_key,
            ),
        )

        config = ObjectsAPIConfig(
            default_objects_api_group=self.config_group,
        )

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=config,
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    def test_update_payment_status(self):
        # We manually create the objects instance, to be in the same state after
        # `plugin.register_submission` was called:
        with get_objects_client(self.config_group) as client:
            data = client.create_object(
                object_data=prepare_data_for_registration(
                    record_data={
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
                    objecttype="http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                    objecttype_version=3,
                )
            )
            objects_url = data["url"]

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
            registration_success=True,
            submitted_data={
                "age": 20,
                "lastname": "My last name",
                "location": [52.36673378967122, 4.893164274470299],
            },
            registration_result={"url": objects_url},
        )

        ObjectsAPIRegistrationData.objects.create(submission=submission)

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            # See the docker compose fixtures for more info on these values:
            "objecttype": "http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            "objecttype_version": 3,
            "upload_submission_csv": True,
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
                    "target_path": ["nested", "submission_payment_amount"],
                },
                {
                    "variable_key": "payment_public_order_ids",
                    "target_path": ["submission_payment_public_ids"],
                },
                # fmt: on
            ],
            "geometry_variable_key": "location",
        }

        SubmissionPaymentFactory.create(
            submission=submission,
            status=PaymentStatus.completed,
            amount=10.01,
            public_order_id="TEST-123",
        )

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
