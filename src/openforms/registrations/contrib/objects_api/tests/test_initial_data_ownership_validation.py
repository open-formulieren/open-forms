from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.test import TestCase, tag

from freezegun import freeze_time

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..plugin import PLUGIN_IDENTIFIER, ObjectsAPIRegistration
from ..typing import RegistrationOptionsV2


@tag("gh-4398")
class DataOwnershipCheckTests(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def test_ownership_check_passes(self):
        # We manually create the objects instance as if it was created upfront by some
        # external party
        with (
            freeze_time("2024-12-04T18:11:00+01:00"),
            get_objects_client(self.api_group) as client,
        ):
            object_data = client.create_object(
                record_data=prepare_data_for_registration(
                    data={"bsn": "111222333", "some": {"path": "foo"}},
                    objecttype_version=1,
                ),
                objecttype_url=(
                    "http://objecttypes-web:8000/api/v2/objecttypes/"
                    "8faed0fa-7864-4409-aa6d-533a37616a9e"
                ),
            )

        submission = SubmissionFactory.create(
            completed_not_preregistered=True,
            initial_data_reference=object_data["uuid"],
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
        )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptionsV2 = {
            "objects_api_group": self.api_group,
            "version": 2,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": True,
            "auth_attribute_path": ["bsn"],
            "variables_mapping": [],
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "transform_to_list": [],
        }

        result = plugin.verify_initial_data_ownership(submission, options)

        # if it doesn't pass, it raises PermissionDenied error instead
        self.assertIsNone(result)

    def test_ownership_check_does_not_pass(self):
        # We manually create the objects instance as if it was created upfront by some
        # external party
        with (
            freeze_time("2024-12-04T18:11:00+01:00"),
            get_objects_client(self.api_group) as client,
        ):
            object_data = client.create_object(
                record_data=prepare_data_for_registration(
                    data={"bsn": "111222333", "some": {"path": "foo"}},
                    objecttype_version=1,
                ),
                objecttype_url=(
                    "http://objecttypes-web:8000/api/v2/objecttypes/"
                    "8faed0fa-7864-4409-aa6d-533a37616a9e"
                ),
            )
        plugin = ObjectsAPIRegistration(PLUGIN_IDENTIFIER)
        options: RegistrationOptionsV2 = {
            "objects_api_group": self.api_group,
            "version": 2,
            "objecttype": UUID("8faed0fa-7864-4409-aa6d-533a37616a9e"),
            "objecttype_version": 1,
            "update_existing_object": True,
            "auth_attribute_path": ["bsn"],
            "variables_mapping": [],
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "transform_to_list": [],
        }

        with self.subTest("other BSN used"):
            submission2 = SubmissionFactory.create(
                completed_not_preregistered=True,
                initial_data_reference=object_data["uuid"],
                auth_info__value="999999999",
                auth_info__attribute=AuthAttribute.bsn,
            )

            with self.assertRaises(PermissionDenied):
                plugin.verify_initial_data_ownership(submission2, options)

        with self.subTest("wrong auth attribute path used"):
            submission2 = SubmissionFactory.create(
                completed_not_preregistered=True,
                initial_data_reference=object_data["uuid"],
                auth_info__value="111222333",
                auth_info__attribute=AuthAttribute.bsn,
            )
            broken_options: RegistrationOptionsV2 = {
                **options,
                "auth_attribute_path": ["nested", "bsn"],
            }

            with self.assertRaises(PermissionDenied):
                plugin.verify_initial_data_ownership(submission2, broken_options)
