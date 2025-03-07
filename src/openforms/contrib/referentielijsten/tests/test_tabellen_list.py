from pathlib import Path

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.vcr import OFVCRMixin

TESTS_DIR = Path(__file__).parent.resolve()
TEST_FILES = TESTS_DIR / "files"


class ReferentielijstTabellenEndpointTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()
        cls.admin_user = StaffUserFactory.create()

        cls.service = ServiceFactory.create(
            slug="referentielijsten", api_root="http://localhost:8004/api/v1/"
        )

    def test_tabellen_list_is_forbidden_for_normal_users(self):
        endpoint = reverse(
            "api:referentielijst-tabellen-list",
            kwargs={"service_slug": "referentielijsten"},
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returned_tabellen_have_the_right_properties(self):
        endpoint = reverse(
            "api:referentielijst-tabellen-list",
            kwargs={"service_slug": "referentielijsten"},
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tabellen = response.json()

        self.assertEqual(
            tabellen,
            [
                {
                    "code": "item-not-geldig-anymore",
                    "naam": "Tabel that contains item not geldig anymore",
                    "isGeldig": False,
                },
                {
                    "code": "not-geldig-anymore",
                    "naam": "Tabel that is not geldig anymore",
                    "isGeldig": False,
                },
                {
                    "code": "tabel-with-many-items",
                    "naam": "Tabel with many items",
                    "isGeldig": True,
                },
                {"code": "tabel1", "naam": "Tabel1", "isGeldig": True},
            ],
        )

    def test_service_not_found(self):
        endpoint = reverse(
            "api:referentielijst-tabellen-list", kwargs={"service_slug": "non-existent"}
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_referentielijsten_api_returns_404(self):
        ServiceFactory.create(
            slug="incorrect-api-root", api_root="http://localhost:8004/incorrect/"
        )
        endpoint = reverse(
            "api:referentielijst-tabellen-list",
            kwargs={"service_slug": "incorrect-api-root"},
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])
