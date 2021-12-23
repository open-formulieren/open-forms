"""
Test the Camunda-plugin specific extra API endpoints.

These endpoints are only used in the form designer.
"""
import uuid
from unittest.mock import patch

from django_camunda.camunda_models import ProcessDefinition
from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory


class ProcessDefinitionsListEndpointTests(APITestCase):
    endpoint = reverse_lazy("api:camunda:process-definitions")

    def test_auth_required(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "openforms.registrations.contrib.camunda.api.get_process_definitions",
        return_value=[],
    )
    def test_staff_user_required(self, mock_get_process_definitions):
        user = UserFactory.create()
        staff_user = StaffUserFactory.create()

        with self.subTest(staff=False):
            self.client.force_authenticate(user=user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(staff=True):
            self.client.force_authenticate(user=staff_user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_subset_process_definition_information_returned(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)
        mock_data = [
            ProcessDefinition(
                id="p1:1:7a249a3d-86f8-4c33-9ce4-fd87d7f2ee91",
                key="p1",
                name="Process 1",
                category="",
                version=1,
                deployment_id=uuid.uuid4(),
                resource="sample.bpmn",
                startable_in_tasklist=True,
                suspended=False,
            ),
            ProcessDefinition(
                id="p1:2:7a249a3d-86f8-4c33-9ce4-fd87d7f2ee91",
                key="p1",
                name="Process 1",
                category="",
                version=2,
                deployment_id=uuid.uuid4(),
                resource="sample.bpmn",
                startable_in_tasklist=True,
                suspended=False,
            ),
            ProcessDefinition(
                id="p2:1:11714efa-b5a2-45a3-904b-31281db1539e",
                key="p2",
                name="Process 2",
                category="",
                version=1,
                deployment_id=uuid.uuid4(),
                resource="sample.bpmn",
                startable_in_tasklist=True,
                suspended=False,
            ),
        ]

        with patch(
            "openforms.registrations.contrib.camunda.api.get_process_definitions",
            return_value=mock_data,
        ):
            response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = [
            {
                "id": "p1:1:7a249a3d-86f8-4c33-9ce4-fd87d7f2ee91",
                "key": "p1",
                "version": 1,
                "name": "Process 1",
            },
            {
                "id": "p1:2:7a249a3d-86f8-4c33-9ce4-fd87d7f2ee91",
                "key": "p1",
                "version": 2,
                "name": "Process 1",
            },
            {
                "id": "p2:1:11714efa-b5a2-45a3-904b-31281db1539e",
                "key": "p2",
                "version": 1,
                "name": "Process 2",
            },
        ]
        self.assertEqual(response.json(), expected)
