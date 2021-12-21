"""
Test the Camunda-plugin specific extra API endpoints.

These endpoints are only used in the form designer.
"""
from unittest.mock import patch

import requests_mock
from django_camunda.camunda_models import ProcessDefinition
from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
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
