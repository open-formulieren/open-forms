import textwrap
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase

import requests_mock
from freezegun import freeze_time

from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..models import ObjectsAPIConfig
from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from .factories import ObjectsAPIGroupConfigFactory


@requests_mock.Mocker()
class ObjectsAPIPaymentStatusUpdateV1Tests(TestCase):
    def test_update_payment_status(self, m):
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
            registration_result={
                "url": "https://objecten.nl/api/v1/objects/111-222-333"
            },
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

        config_group = ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v1/",
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
        )

        m.patch(
            "https://objecten.nl/api/v1/objects/111-222-333",
            json={},  # Unused in our case, but required as .json() is called on the response
            status_code=200,
        )
        m.get(
            "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
            json={
                "url": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377"
            },
            status_code=200,
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with freeze_time("2020-02-02"):
            with patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ):
                plugin.update_payment_status(
                    submission,
                    {
                        "version": 1,
                        "objects_api_group": config_group,
                        "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
                        "objecttype_version": 1,
                    },
                )

        self.assertEqual(len(m.request_history), 2)

        patch_request = m.request_history[1]
        body = patch_request.json()

        self.assertEqual(
            body["record"]["data"]["payment"],
            {
                "completed": True,
                "amount": 10.01,
                "public_order_ids": ["TEST-123"],
                "payment_ids": ["12345"],
            },
        )
        self.assertEqual(body["record"]["startAt"], "2020-02-02")

    def test_template_overwritten_through_options(self, m):
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
            registration_result={
                "url": "https://objecten.nl/api/v1/objects/111-222-333"
            },
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

        config_group = ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v1/",
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
        )

        m.patch(
            "https://objecten.nl/api/v1/objects/111-222-333",
            json={},  # Unused in our case, but required as .json() is called on the response
            status_code=200,
        )
        m.get(
            "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
            json={
                "url": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377"
            },
            status_code=200,
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        with freeze_time("2020-02-02"):
            with patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ):
                plugin.update_payment_status(
                    submission,
                    {
                        "version": 1,
                        "objects_api_group": config_group,
                        "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
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

        self.assertEqual(len(m.request_history), 2)

        patch_request = m.request_history[1]
        body = patch_request.json()

        self.assertEqual(
            body["record"]["data"]["payment"],
            {
                "completed": True,
                "amount": 10,
                "public_order_ids": ["TEST-123"],
                "payment_ids": ["12345"],
            },
        )
        self.assertEqual(body["record"]["startAt"], "2020-02-02")

    def test_no_template_specified(self, m):
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
            registration_result={
                "url": "https://objecten.nl/api/v1/objects/111-222-333"
            },
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

        config_group = ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objecten.nl/api/v1/",
            objecttypes_service__api_root="https://objecttypen.nl/api/v1/",
        )

        m.patch(
            "https://objecten.nl/api/v1/objects/111-222-333",
            json={},  # Unused in our case, but required as .json() is called on the response
            status_code=200,
        )
        m.get(
            "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377",
            json={
                "url": "https://objecttypen.nl/api/v1/objecttypes/f3f1b370-97ed-4730-bc7e-ebb20c230377"
            },
            status_code=200,
        )

        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)

        with freeze_time("2020-02-02"):
            with patch(
                "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
                return_value=config,
            ):
                plugin.update_payment_status(
                    submission,
                    {
                        "version": 1,
                        "objects_api_group": config_group,
                        "objecttype": UUID("f3f1b370-97ed-4730-bc7e-ebb20c230377"),
                        "objecttype_version": 1,
                    },
                )

        self.assertEqual(len(m.request_history), 0)
