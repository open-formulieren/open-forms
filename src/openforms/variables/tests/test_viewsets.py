from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory

from ..constants import DataMappingTypes, ServiceFetchMethods
from .factories import ServiceFetchConfigurationFactory


class ServiceFetchConfigurationAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()
        cls.admin_user = StaffUserFactory.create()

    def test_service_fetch_configuration_list_is_forbidden_for_normal_users(self):
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_service_fetch_configuration_list_returns_a_list_to_admin_users(self):
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(), {"count": 0, "next": None, "previous": None, "results": []}
        )

    def test_service_fetch_configuration_have_the_right_properties(self):
        config = ServiceFetchConfigurationFactory.create(
            name="Service fetch configuration 1",
            path="/foo",
            method=ServiceFetchMethods.post,
            headers={"X-Foo": "bar"},
            query_params={"param": "value"},
            body={"foo": "bar"},
            data_mapping_type=DataMappingTypes.jq,
            mapping_expression=".foo",
        )
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        expected = {
            "id": config.pk,
            "name": "Service fetch configuration 1",
            "service": f"http://testserver{reverse('api:service-detail', kwargs={'pk': config.service.pk})}",
            "path": "/foo",
            "method": ServiceFetchMethods.post.value,
            "headers": {"X-Foo": "bar"},
            "query_params": {"param": "value"},
            "body": {"foo": "bar"},
            "data_mapping_type": DataMappingTypes.jq.value,
            "mapping_expression": ".foo",
        }

        self.assertEqual(response.data["results"][0], expected)
