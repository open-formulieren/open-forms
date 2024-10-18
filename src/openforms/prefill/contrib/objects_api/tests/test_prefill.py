from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from django.urls import reverse

from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.contrib.objects_api.clients import get_objects_client
from openforms.contrib.objects_api.helpers import prepare_data_for_registration
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import FormVariableFactory
from openforms.logging.models import TimelineLogProxy
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.registrations.contrib.objects_api.plugin import ObjectsAPIRegistration
from openforms.registrations.contrib.objects_api.typing import RegistrationOptionsV2
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.tests.vcr import OFVCRMixin

from ....service import prefill_variables

VCR_TEST_FILES = Path(__file__).parent / "files"


class ObjectsAPIPrefillPluginTests(OFVCRMixin, SubmissionsMixin, APITestCase):
    """This test case requires the Objects & Objecttypes API to be running.
    See the relevant Docker compose in the ``docker/`` folder.
    """

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

    def test_prefill_values_happy_flow(self):
        # We manually create the objects instance as if it was created upfront by some external party
        with get_objects_client(self.objects_api_group) as client:
            created_obj = client.create_object(
                record_data=prepare_data_for_registration(
                    data={
                        "name": {"last.name": "My last name"},
                        "age": 45,
                    },
                    objecttype_version=3,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )

        submission = SubmissionFactory.from_components(
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
                "objects_api_group": self.objects_api_group.pk,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(TimelineLogProxy.objects.count(), 1)
        logs = TimelineLogProxy.objects.get()

        self.assertEqual(logs.extra_data["log_event"], "prefill_retrieve_success")
        self.assertEqual(logs.extra_data["plugin_id"], "objects_api")
        self.assertEqual(state.variables["lastName"].value, "My last name")
        self.assertEqual(state.variables["age"].value, 45)

    def test_prefill_values_when_reference_not_found(self):
        submission = SubmissionFactory.from_components(
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
                "objects_api_group": self.objects_api_group.pk,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(TimelineLogProxy.objects.count(), 1)
        logs = TimelineLogProxy.objects.get()

        self.assertEqual(logs.extra_data["log_event"], "prefill_retrieve_failure")
        self.assertEqual(logs.extra_data["plugin_id"], "objects_api")
        self.assertIsNone(state.variables["lastName"].value)
        self.assertIsNone(state.variables["age"].value)

    def test_prefill_values_when_reference_returns_empty_values(self):
        # We manually create the objects instance as if it was created upfront by some external party
        with get_objects_client(self.objects_api_group) as client:
            created_obj = client.create_object(
                record_data=prepare_data_for_registration(
                    data={},
                    objecttype_version=3,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )

        submission = SubmissionFactory.from_components(
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
                "objects_api_group": self.objects_api_group.pk,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(TimelineLogProxy.objects.count(), 1)
        logs = TimelineLogProxy.objects.get()

        self.assertEqual(logs.extra_data["log_event"], "prefill_retrieve_empty")
        self.assertEqual(logs.extra_data["plugin_id"], "objects_api")
        self.assertIsNone(state.variables["lastName"].value)
        self.assertIsNone(state.variables["age"].value)

    def test_prefilled_values_are_updated_in_the_object(self):
        """
        This tests that a created object in the ObjectsAPI prefills the form variables (components) as
        expected and then (in the same submission) we make sure that we can update the object.
        """
        # We manually create the objects instance as if it was created upfront by some external party
        with get_objects_client(self.objects_api_group) as client:
            created_obj = client.create_object(
                record_data=prepare_data_for_registration(
                    data={
                        "name": {"last.name": "My last name"},
                        "age": 45,
                    },
                    objecttype_version=3,
                ),
                objecttype_url="http://objecttypes-web:8000/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            )

        submission = SubmissionFactory.from_components(
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
            form__registration_backend="objects_api",
            with_report=False,
        )

        user = SuperUserFactory.create()
        self.client.force_login(user=user)
        self._add_submission_to_session(submission)

        FormVariableFactory.create(
            form=submission.form,
            prefill_plugin="objects_api",
            prefill_options={
                "objects_api_group": self.objects_api_group.pk,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "lastName", "target_path": ["name", "last.name"]},
                    {"variable_key": "age", "target_path": ["age"]},
                ],
            },
        )

        prefill_variables(submission=submission)

        # Update the prefilled data
        self.client.put(
            reverse(
                "api:submission-steps-detail",
                kwargs={
                    "submission_uuid": submission.uuid,
                    "step_uuid": submission.form.formstep_set.get().uuid,
                },
            ),
            {"data": {"age": 51, "lastName": "New last name"}},
        )

        v2_options: RegistrationOptionsV2 = {
            "version": 2,
            "objects_api_group": self.objects_api_group,
            # See the docker compose fixtures for more info on these values:
            "objecttype": UUID("8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"),
            "objecttype_version": 3,
            "variables_mapping": [
                {
                    "variable_key": "age",
                    "target_path": ["age"],
                },
                {"variable_key": "lastName", "target_path": ["name", "last.name"]},
            ],
            "update_existing_object": True,
        }

        submission = Submission.objects.get(pk=submission.pk)
        plugin = ObjectsAPIRegistration("objects_api")
        result = plugin.register_submission(submission, v2_options)

        assert result is not None

        self.assertTrue(result["uuid"], created_obj["uuid"])
        self.assertEqual(result["record"]["data"]["age"], 51)
        self.assertEqual(result["record"]["data"]["name"]["last.name"], "New last name")
