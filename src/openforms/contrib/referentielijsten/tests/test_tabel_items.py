from pathlib import Path

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.vcr import OFVCRMixin

TESTS_DIR = Path(__file__).parent.resolve()
TEST_FILES = TESTS_DIR / "files"


class ReferentielijstTabelItemsEndpointTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()
        cls.admin_user = StaffUserFactory.create()

        cls.service = ServiceFactory.create(
            slug="referentielijsten", api_root="http://localhost:8004/api/v1/"
        )

    def test_tabel_items_list_is_forbidden_for_normal_users(self):
        endpoint = reverse(
            "api:referentielijst-tabel-items-list",
            kwargs={"service_slug": "referentielijsten", "tabel_code": "tabel1"},
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returned_tabel_items_have_the_right_properties(self):
        endpoint = reverse(
            "api:referentielijst-tabel-items-list",
            kwargs={"service_slug": "referentielijsten", "tabel_code": "tabel1"},
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)
        items = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            items,
            [
                {"code": "option2", "naam": "Option 2", "isGeldig": True},
                {"code": "option1", "naam": "Option 1", "isGeldig": True},
            ],
        )

    def test_empty_tabel_items(self):
        endpoint = reverse(
            "api:referentielijst-tabel-items-list",
            kwargs={
                "service_slug": "referentielijsten",
                "tabel_code": "non_existing_tabel",
            },
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_invalid_tabel_item(self):
        endpoint = reverse(
            "api:referentielijst-tabel-items-list",
            kwargs={
                "service_slug": "referentielijsten",
                "tabel_code": "item-not-geldig-anymore",
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
                    "isGeldig": False,
                    "naam": "Not geldig option",
                }
            ],
        )

    def test_referentielijsten_api_returns_404(self):
        ServiceFactory.create(
            slug="incorrect-api-root", api_root="http://localhost:8004/incorrect/"
        )
        endpoint = reverse(
            "api:referentielijst-tabel-items-list",
            kwargs={
                "service_slug": "incorrect-api-root",
                "tabel_code": "tabel1",
            },
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])
