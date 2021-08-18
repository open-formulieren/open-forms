from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory

from .factories import ProductFactory


class ProductListEndpointTests(APITestCase):
    list_url = reverse_lazy("api:product-list")

    def test_auth_required(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_user(self):
        user = UserFactory.create()
        assert user.is_staff is False
        self.client.force_authenticate(user=user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_data_staff_user(self):
        product = ProductFactory.create(name="sample", price="10.00")
        user = StaffUserFactory.create()

        self.client.force_authenticate(user=user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data,
            [
                {
                    "uuid": str(product.uuid),
                    "url": f"http://testserver{reverse('api:product-detail', kwargs={'uuid': product.uuid})}",
                    "name": "sample",
                    "price": "10.00",
                }
            ],
        )


class ProductRetrieveEndpointTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.product = ProductFactory.create()
        cls.detail_url = reverse(
            "api:product-detail", kwargs={"uuid": cls.product.uuid}
        )

    def test_auth_required(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_user(self):
        user = UserFactory.create()
        assert user.is_staff is False
        self.client.force_authenticate(user=user)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_staff_user(self):
        user = StaffUserFactory.create()

        self.client.force_authenticate(user=user)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data,
            {
                "uuid": str(self.product.uuid),
                "url": f"http://testserver{self.detail_url}",
                "name": self.product.name,
                "price": str(self.product.price),
            },
        )
