from pathlib import Path

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.vcr import OFVCRMixin

TESTS_DIR = Path(__file__).parent.resolve()
TEST_FILES = TESTS_DIR / "files"


class ReferenceListsTablesEndpointTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES

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

    def test_tables_list_is_forbidden_for_normal_users(self):
        endpoint = reverse(
            "api:reference-lists-tables-list",
            kwargs={"service_slug": "reference-lists"},
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returned_tables_have_the_right_properties(self):
        endpoint = reverse(
            "api:reference-lists-tables-list",
            kwargs={"service_slug": "reference-lists"},
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tables = response.json()

        self.assertEqual(
            tables,
            [
                {
                    "code": "item-not-geldig-anymore",
                    "name": "Tabel that contains item not geldig anymore",
                    "isValid": True,
                },
                {
                    "code": "not-geldig-anymore",
                    "name": "Tabel that is not geldig anymore",
                    "isValid": False,
                },
                {
                    "code": "tabel-with-many-items",
                    "name": "Tabel with many items",
                    "isValid": True,
                },
                {"code": "tabel1", "name": "Tabel1", "isValid": True},
            ],
        )

    def test_service_not_found(self):
        endpoint = reverse(
            "api:reference-lists-tables-list", kwargs={"service_slug": "non-existent"}
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_url(self):
        ServiceFactory.create(
            slug="incorrect-api-root",
            api_root="http://localhost:8004/incorrect/",
            auth_type=AuthTypes.no_auth,
        )
        endpoint = reverse(
            "api:reference-lists-tables-list",
            kwargs={"service_slug": "incorrect-api-root"},
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])
