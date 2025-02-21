import json

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
        cls.user_with_perms = UserFactory.create(user_permissions=["forms.change_form"])
        cls.staff_user_without_perms = StaffUserFactory.create()
        cls.admin_user = StaffUserFactory(user_permissions=["forms.change_form"])

    def test_service_fetch_configuration_list_is_forbidden_for_normal_users(self):
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_service_fetch_configuration_list_is_forbidden_for_normal_users_with_perms(
        self,
    ):
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.user_with_perms)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_service_fetch_configuration_list_is_forbidden_for_staff_users_without_perms(
        self,
    ):
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.staff_user_without_perms)

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
            query_params={"param": ["value"]},
            body={"foo": "bar"},
            data_mapping_type=DataMappingTypes.jq,
            mapping_expression=".foo",
            cache_timeout=50,
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
            "query_params": {"param": ["value"]},
            "body": {"foo": "bar"},
            "data_mapping_type": DataMappingTypes.jq.value,
            "mapping_expression": ".foo",
            "cache_timeout": 50,
        }

        self.assertEqual(response.data["results"][0], expected)

    def test_service_fetch_configuration_list_returns_data_using_correct_text_case(
        self,
    ):
        config = ServiceFetchConfigurationFactory.create(
            name="Service fetch configuration 1",
            method=ServiceFetchMethods.post,
            query_params={
                "snake_case": ["snake_case_data"],
                "camelCase": ["camelCaseData"],
            },
            body={"snake_case": "snake_case_data", "camelCase": "camelCaseData"},
        )
        endpoint = reverse("api:servicefetchconfiguration-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        content = json.loads(response.content)
        expected = {
            "id": config.pk,
            "name": "Service fetch configuration 1",
            "service": f"http://testserver{reverse('api:service-detail', kwargs={'pk': config.service.pk})}",
            "path": "",
            "method": ServiceFetchMethods.post.value,
            "headers": {},
            "queryParams": {
                "snake_case": ["snake_case_data"],
                "camelCase": ["camelCaseData"],
            },
            "body": {"snake_case": "snake_case_data", "camelCase": "camelCaseData"},
            "dataMappingType": "",
            "mappingExpression": None,
            "cacheTimeout": None,
        }

        self.assertEqual(content["results"][0], expected)
