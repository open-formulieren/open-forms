from pathlib import Path

from furl import furl
from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..tests.factories import ZGWApiGroupConfigFactory


class CatalogusAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"
    endpoint = reverse_lazy("api:zgw_apis:catalogi-list")

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

        test_catalogus = [obj for obj in response.json() if obj["domein"] == "TEST"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(test_catalogus), 1)


class GetInformatieObjecttypesViewTests(OFVCRMixin, APITestCase):

    endpoint = reverse_lazy("api:zgw_apis:iotypen-list")
    VCR_TEST_FILES = Path(__file__).parent / "files"

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
        url = furl(self.endpoint)
        url.args["zgw_api_group"] = "INVALID"
        self.client.force_login(user)

        response = self.client.get(url.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_zgw_api_group(self):
        user = StaffUserFactory.create()
        self.client.force_login(user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_with_explicit_zgw_api_group(self):
        user = StaffUserFactory.create()
        url = furl(self.endpoint)
        url.args["zgw_api_group"] = self.zgw_api_group.pk
        self.client.force_login(user)

        response = self.client.get(url.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(len(data), 3)

    def test_retrieve_filter_by_catalogus_missing_param(self):
        user = StaffUserFactory.create()
        url = furl(self.endpoint)
        url.args["zgw_api_group"] = self.zgw_api_group.pk
        url.args["catalogus_domein"] = "TEST"
        # We don't add `catalogus_rsin` here
        self.client.force_login(user)

        response = self.client.get(url.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_filter_by_catalogus(self):
        user = StaffUserFactory.create()
        url = furl(self.endpoint)
        url.args["zgw_api_group"] = self.zgw_api_group.pk
        url.args["catalogus_domein"] = "TEST"
        url.args["catalogus_rsin"] = "000000000"
        self.client.force_login(user)

        response = self.client.get(url.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(len(data), 3)
