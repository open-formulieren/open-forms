from pathlib import Path

from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.utils.tests.vcr import OFVCRMixin

from .factories import ZGWApiGroupConfigFactory


class ZaakTypenAPIEndpointTests(OFVCRMixin, APITestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"
    endpoint = reverse_lazy("api:zgw_api:zaaktypen-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # create services for the docker-compose Open Zaak instance.
        _credentials = {
            "auth_type": AuthTypes.zgw,
            "client_id": "test_client_id",
            "secret": "test_secret_key",
        }
        zaken_service = ServiceFactory.create(
            api_root="http://localhost:8003/zaken/api/v1/",
            api_type=APITypes.zrc,
            **_credentials,
        )
        documenten_service = ServiceFactory.create(
            api_root="http://localhost:8003/documenten/api/v1/",
            api_type=APITypes.drc,
            **_credentials,
        )
        catalogi_service = ServiceFactory.create(
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            **_credentials,
        )
        cls.zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service=zaken_service,
            drc_service=documenten_service,
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

    def test_list_zaaktypen(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(
            self.endpoint, data={"zgw_api_group": self.zgw_group.pk}
        )

        test_zaaktype = next(
            obj for obj in response.json() if obj["zaaktype"]["omschrijving"] == "Test"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(test_zaaktype["catalogus"]["domein"], "TEST")
