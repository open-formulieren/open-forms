from pathlib import Path

from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.feature_flags import enable_feature_flag
from openforms.utils.tests.vcr import OFVCRMixin

from ..tests.factories import ZGWApiGroupConfigFactory

TEST_FILES = Path(__file__).parent / "files"


class CatalogusAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy("api:zgw_apis:catalogue-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # create services for the docker-compose Open Zaak instance.
        catalogi_service = ServiceFactory.create(
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        cls.zgw_api_group = ZGWApiGroupConfigFactory.create(
            ztc_service=catalogi_service,
        )

    def test_auth_required(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_required(self):
        user = UserFactory.create()

        with self.subTest(staff=False):
            self.client.force_authenticate(user=user)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_catalogus(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(
            self.endpoint,
            data={
                "zgw_api_group": self.zgw_api_group.pk,
            },
        )

        test_catalogus = [obj for obj in response.json() if obj["domain"] == "TEST"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(test_catalogus), 1)


class GetCaseTypesViewTests(OFVCRMixin, APITestCase):
    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy("api:zgw_apis:case-type-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_api_group = ZGWApiGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def test_must_be_logged_in_as_admin(self):
        user = UserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_filters(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint,
            {
                "zgw_api_group": "INVALID",
                "catalogue_url": "not-a-url",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_param_names = {
            item["name"] for item in response.json()["invalidParams"]
        }
        self.assertEqual(invalid_param_names, {"zgwApiGroup", "catalogueUrl"})

    def test_missing_filters(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_param_names = {
            item["name"] for item in response.json()["invalidParams"]
        }
        self.assertEqual(invalid_param_names, {"zgwApiGroup", "catalogueUrl"})

    def test_find_case_types_deduplicates_versions(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint,
            {
                "zgw_api_group": self.zgw_api_group.pk,
                "catalogue_url": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "catalogussen/bd58635c-793e-446d-a7e0-460d7b04829d"
                ),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertGreaterEqual(len(results), 1)
        identificaties = {ct["identification"] for ct in results}
        # assert versions are de-duplicated (multiple versions have the same
        # identification)
        self.assertEqual(len(identificaties), len(results))

    def test_drafts_are_not_included_by_default(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint,
            {
                "zgw_api_group": self.zgw_api_group.pk,
                # DRAFTS catalogus
                "catalogue_url": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "catalogussen/aa0e0a50-33f6-4473-99a1-b92bab94e749"
                ),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertEqual(results, [])

    @enable_feature_flag("ZGW_APIS_INCLUDE_DRAFTS")
    def test_drafts_included_with_feature_flag_on(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint,
            {
                "zgw_api_group": self.zgw_api_group.pk,
                # DRAFTS catalogus
                "catalogue_url": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "catalogussen/aa0e0a50-33f6-4473-99a1-b92bab94e749"
                ),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertNotEqual(results, [])
        for item in results:
            with self.subTest(item=item):
                self.assertFalse(item["isPublished"])


class GetInformatieObjecttypesViewTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = TEST_FILES
    endpoint = reverse_lazy("api:zgw_apis:iotypen-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # create services for the docker-compose Open Zaak instance.
        catalogi_service = ServiceFactory.create(
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        cls.zgw_api_group = ZGWApiGroupConfigFactory.create(
            ztc_service=catalogi_service,
        )

    def test_must_be_logged_in_as_admin(self):
        user = UserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_with_invalid_zgw_api_group(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint, {"zgw_api_group": "INVALID"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_zgw_api_group(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_with_explicit_zgw_api_group(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint,
            {
                "zgw_api_group": self.zgw_api_group.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertGreaterEqual(len(data), 3)

    def test_retrieve_filter_by_catalogus(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(
            self.endpoint,
            {
                "zgw_api_group": self.zgw_api_group.pk,
                "catalogus_url": "http://localhost:8003/catalogi/api/v1/catalogussen/bd58635c-793e-446d-a7e0-460d7b04829d",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(len(data), 3)
