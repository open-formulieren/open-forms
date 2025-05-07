from django.test import TestCase
from django.urls import reverse_lazy


class GenericJsonApiTests(TestCase):
    endpoint = reverse_lazy("api:registrations_generic_json:fixed_metadata_variables")

    def test_get(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), list))
