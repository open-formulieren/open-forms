from unittest.mock import patch

from django.core.exceptions import PermissionDenied

from rest_framework.test import APITestCase

from openforms.authentication.service import AuthAttribute
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import FormVariableFactory
from openforms.logging.models import TimelineLogProxy
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.tests.vcr import OFVCRMixin

from ....service import prefill_variables


class ObjectsAPIPrefillPluginTests(OFVCRMixin, SubmissionsMixin, APITestCase):
    """This test case requires the Objects & Objecttypes API to be running.
    See the relevant Docker compose in the ``docker/`` folder.
    """

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

    def test_prefill_values_happy_flow(self):
        # We manually create the objects instance as if it was created upfront by some external party
        with get_objects_client(self.objects_api_group) as client:
            created_obj = client.create_object(
                record_data=prepare_data_for_registration(
                    data={
                        "name": {"last.name": "My last name"},
                        "age": 45,
                        "bsn": "111222333",
                    },
                    objecttype_version=3,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )

        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=created_obj["uuid"],
            components_list=[
                {
                    "type": "textfield",
                    "key": "age",
                    "label": "Age",
                },
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Last name",
                },
            ],
        )
        FormVariableFactory.create(
            form=submission.form,
            prefill_plugin="objects_api",
            prefill_options={
                "objects_api_group": self.objects_api_group.identifier,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
                "auth_attribute_path": ["bsn"],
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(TimelineLogProxy.objects.count(), 2)
        ownership_check_log, prefill_log = TimelineLogProxy.objects.all()

        self.assertEqual(
            ownership_check_log.extra_data["log_event"],
            "object_ownership_check_success",
        )
        self.assertEqual(ownership_check_log.extra_data["plugin_id"], "objects_api")
        self.assertEqual(
            prefill_log.extra_data["log_event"], "prefill_retrieve_success"
        )
        self.assertEqual(prefill_log.extra_data["plugin_id"], "objects_api")
        self.assertEqual(state.variables["lastName"].value, "My last name")
        self.assertEqual(state.variables["age"].value, "45")

    def test_prefill_values_when_reference_not_found(self):
        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference="048a37ca-a602-4158-9e60-9f06f3e47e2a",
            components_list=[
                {
                    "type": "textfield",
                    "key": "age",
                    "label": "Age",
                },
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Last name",
                },
            ],
        )
        FormVariableFactory.create(
            form=submission.form,
            prefill_plugin="objects_api",
            prefill_options={
                "objects_api_group": self.objects_api_group.identifier,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
                "auth_attribute_path": ["bsn"],
            },
        )

        with self.assertRaises(PermissionDenied):
            prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_unsaved=True)

        self.assertEqual(TimelineLogProxy.objects.count(), 1)
        logs = TimelineLogProxy.objects.get()

        self.assertEqual(logs.extra_data["log_event"], "prefill_retrieve_failure")
        self.assertEqual(logs.extra_data["plugin_id"], "objects_api")
        self.assertEqual(data["lastName"], "")
        self.assertEqual(data["age"], "")

    def test_prefill_values_when_reference_returns_empty_values(self):
        # We manually create the objects instance as if it was created upfront by some external party
        with get_objects_client(self.objects_api_group) as client:
            created_obj = client.create_object(
                record_data=prepare_data_for_registration(
                    data={"bsn": "111222333"},
                    objecttype_version=3,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )

        submission = SubmissionFactory.from_components(
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference=created_obj["uuid"],
            components_list=[
                {
                    "type": "textfield",
                    "key": "age",
                    "label": "Age",
                },
                {
                    "type": "textfield",
                    "key": "lastName",
                    "label": "Last name",
                },
            ],
        )
        FormVariableFactory.create(
            form=submission.form,
            prefill_plugin="objects_api",
            prefill_options={
                "objects_api_group": self.objects_api_group.identifier,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
                "auth_attribute_path": ["bsn"],
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_unsaved=True)

        self.assertEqual(TimelineLogProxy.objects.count(), 2)
        ownership_check_log, prefill_log = TimelineLogProxy.objects.all()

        self.assertEqual(
            ownership_check_log.extra_data["log_event"],
            "object_ownership_check_success",
        )
        self.assertEqual(ownership_check_log.extra_data["plugin_id"], "objects_api")
        self.assertEqual(prefill_log.extra_data["log_event"], "prefill_retrieve_empty")
        self.assertEqual(prefill_log.extra_data["plugin_id"], "objects_api")
        self.assertEqual(data["lastName"], "")
        self.assertEqual(data["age"], "")
