from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.vcr import OFVCRMixin


class ReferenceListsTableItemsEndpointTests(OFVCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()
        cls.admin_user = StaffUserFactory.create()

        cls.service = ServiceFactory.create(
            slug="reference-lists",
            api_root="http://localhost:8004/api/v1/",
            auth_type=AuthTypes.no_auth,
        )

    def test_table_items_list_is_forbidden_for_normal_users(self):
        endpoint = reverse(
            "api:reference-lists-table-items-list",
            kwargs={"service_slug": "reference-lists", "table_code": "tabel1"},
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returned_table_items_have_the_right_properties(self):
        endpoint = reverse(
            "api:reference-lists-table-items-list",
            kwargs={"service_slug": "reference-lists", "table_code": "tabel1"},
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)
        items = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            items,
            [
                {"code": "option2", "name": "Option 2", "isValid": True},
                {"code": "option1", "name": "Option 1", "isValid": True},
            ],
        )

    def test_empty_table_items(self):
        endpoint = reverse(
            "api:reference-lists-table-items-list",
            kwargs={
                "service_slug": "reference-lists",
                "table_code": "non_existing_tabel",
            },
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_invalid_table_item(self):
        endpoint = reverse(
            "api:reference-lists-table-items-list",
            kwargs={
                "service_slug": "reference-lists",
                "table_code": "item-not-geldig-anymore",
            },
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)
        items = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            items,
            [
                {
                    "code": "not_geldig_option",
                    "isValid": False,
                    "name": "Not geldig option",
                }
            ],
        )
