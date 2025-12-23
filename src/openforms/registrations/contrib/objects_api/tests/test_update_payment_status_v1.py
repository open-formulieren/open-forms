import textwrap
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase

from freezegun import freeze_time

from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ObjectsAPIConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration


class ObjectsAPIPaymentStatusUpdateV1Tests(OFVCRMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.config_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
        )

        # We manually create the objects instance, to be in the same state after
        # `plugin.register_submission` was called:
        with get_objects_client(self.config_group) as client:
            data = client.create_object(
                record_data=prepare_data_for_registration(
                    data={},
                    objecttype_version=1,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8faed0fa-7864-4409-aa6d-533a37616a9e",
            )
            # Because of the nginx reverse proxy, we need to set the correct
            # host as this URL will be used by the plugin to update the payment status:
            self.objects_url = data["url"].replace("objects-web:8000", "localhost:8002")

    def test_update_payment_status(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "test",
                    "type": "textfield",
                },
            ],
            registration_success=True,
            submitted_data={"test": "some test data"},
            language_code="en",
            registration_result={"url": self.objects_url},
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

        config = ObjectsAPIConfig(
            payment_status_update_json=textwrap.dedent(
                """
                {
                    "payment": {
                        "completed": {% if payment.completed %}true{% else %}false{% endif %},
                        "amount": {{ payment.amount }},
                        "public_order_ids": [{% for order_id in payment.public_order_ids%}"{{ order_id|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}],
                        "payment_ids": [{% for payment_id in payment.provider_payment_ids%}"{{ payment_id|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}]
                    }
                }"""
            ),
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with (
            freeze_time("2020-02-02"),
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
        ):
            result = plugin.update_payment_status(
                submission,
                {
                    "version": 1,
                    "objects_api_group": self.config_group,
                    "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                    "objecttype_version": 1,
                },
            )

        self.assertEqual(
            result["record"]["data"]["payment"],
            {
                "completed": True,
                "amount": 10.01,
                "public_order_ids": ["TEST-123"],
                "payment_ids": ["12345"],
            },
        )
        self.assertEqual(result["record"]["startAt"], "2020-02-02")

    def test_template_overwritten_through_options(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "test",
                    "type": "textfield",
                },
            ],
            registration_success=True,
            submitted_data={"test": "some test data"},
            language_code="en",
            registration_result={"url": self.objects_url},
            form__payment_backend="demo",
            form__product__price=10,
        )
        SubmissionPaymentFactory.create(
            submission=submission,
            status=PaymentStatus.completed,
            amount=10,
            public_order_id="TEST-123",
            provider_payment_id="12345",
        )

        config = ObjectsAPIConfig()

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with (
            freeze_time("2020-02-02"),
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
        ):
            result = plugin.update_payment_status(
                submission,
                {
                    "version": 1,
                    "objects_api_group": self.config_group,
                    "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                    "objecttype_version": 1,
                    "payment_status_update_json": textwrap.dedent(
                        """
                {
                    "payment": {
                        "completed": {% if payment.completed %}true{% else %}false{% endif %},
                        "amount": {{ payment.amount }},
                        "public_order_ids": [{% for order_id in payment.public_order_ids%}"{{ order_id|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}],
                        "payment_ids": [{% for payment_id in payment.provider_payment_ids%}"{{ payment_id|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}]
                    }
                }"""
                    ),
                },
            )

        self.assertEqual(
            result["record"]["data"]["payment"],
            {
                "completed": True,
                "amount": 10,
                "public_order_ids": ["TEST-123"],
                "payment_ids": ["12345"],
            },
        )
        self.assertEqual(result["record"]["startAt"], "2020-02-02")

    def test_no_template_specified(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "test",
                    "type": "textfield",
                },
            ],
            registration_success=True,
            submitted_data={"test": "some test data"},
            language_code="en",
            registration_result={"url": self.objects_url},
        )
        SubmissionPaymentFactory.create(
            submission=submission,
            status=PaymentStatus.completed,
            amount=10,
            public_order_id="TEST-123",
        )

        config = ObjectsAPIConfig(
            payment_status_update_json="",
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with (
            freeze_time("2020-02-02"),
            patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ),
        ):
            result = plugin.update_payment_status(
                submission,
                {
                    "version": 1,
                    "objects_api_group": self.config_group,
                    "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
                    "objecttype_version": 1,
                },
            )

        self.assertIsNone(result)
