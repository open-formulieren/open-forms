from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.config.models import GlobalConfiguration


class AccessControlTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()
        cls.admin_user = StaffUserFactory.create()

    def test_service_list_is_forbidden_for_normal_users(self):
        endpoint = reverse("api:service-list")
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_service_list_returns_a_list_to_admin_users(self):
        endpoint = reverse("api:service-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_service_list_filter_by_referentielijsten(self):
        config = GlobalConfiguration.get_solo()
        config.referentielijsten_services.set(
            [ServiceFactory.create(label="Referentielijsten", slug="referentielijsten")]
        )
        config.save()
        endpoint = reverse("api:service-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint, {"type": "referentielijsten"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        services = response.json()

        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]["slug"], "referentielijsten")

    def test_returned_services_have_the_right_properties(self):
        expected_service = ServiceFactory.create()
        endpoint = reverse("api:service-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service = response.json()[0]
        self.assertEqual(
            service["url"],
            f"http://testserver{reverse('api:service-detail', kwargs={'pk': expected_service.pk})}",
        )
        self.assertEqual(service["label"], expected_service.label)
        self.assertEqual(service["apiRoot"], expected_service.api_root)
        self.assertEqual(service["apiType"], expected_service.api_type)
