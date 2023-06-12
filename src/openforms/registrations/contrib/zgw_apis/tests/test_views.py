from unittest.mock import patch

import requests_mock
from furl import furl
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zds_client.oas import schema_fetcher
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.schema_mock import mock_service_oas_get

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)


@requests_mock.Mocker()
class GetInformatieObjecttypesView(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_group1 = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken-1.nl/api/v1/",
            zrc_service__oas="https://zaken-1.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten-1.nl/api/v1/",
            drc_service__oas="https://documenten-1.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus-1.nl/api/v1/",
            ztc_service__oas="https://catalogus-1.nl/api/v1/schema/openapi.yaml",
        )
        cls.zgw_group2 = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken-2.nl/api/v1/",
            zrc_service__oas="https://zaken-2.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten-2.nl/api/v1/",
            drc_service__oas="https://documenten-2.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus-2.nl/api/v1/",
            ztc_service__oas="https://catalogus-2.nl/api/v1/schema/openapi.yaml",
        )

    def setUp(self):
        super().setUp()
        # reset cache to keep request_history indexes consistent
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)

    def install_mocks(self, m):
        mock_service_oas_get(m, "https://catalogus-1.nl/api/v1/", "catalogi")
        informatieobjecttypen1 = [
            generate_oas_component(
                "catalogi",
                "schemas/InformatieObjectType",
                url="https://catalogus-1.nl/api/v1/informatieobjecttypen/111",
                catalogus="https://catalogus-1.nl/api/v1/catalogussen/111",
            ),
            generate_oas_component(
                "catalogi",
                "schemas/InformatieObjectType",
                url="https://catalogus-1.nl/api/v1/informatieobjecttypen/222",
                catalogus="https://catalogus-1.nl/api/v1/catalogussen/111",
            ),
        ]
        m.get(
            "https://catalogus-1.nl/api/v1/catalogussen",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/Catalogus",
                        url="https://catalogus-1.nl/api/v1/catalogussen/111",
                        volgnummer=1,
                        informatieobjecttypen=informatieobjecttypen1,
                    ),
                ],
            },
        )
        m.get(
            "https://catalogus-1.nl/api/v1/informatieobjecttypen",
            status_code=200,
            json={
                "count": 2,
                "next": None,
                "previous": None,
                "results": informatieobjecttypen1,
            },
        )

        mock_service_oas_get(m, "https://catalogus-2.nl/api/v1/", "catalogi")
        informatieobjecttypen2 = [
            generate_oas_component(
                "catalogi",
                "schemas/InformatieObjectType",
                url="https://catalogus-2.nl/api/v1/informatieobjecttypen/111",
                catalogus="https://catalogus-2.nl/api/v1/catalogussen/111",
            ),
        ]
        m.get(
            "https://catalogus-2.nl/api/v1/catalogussen",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/Catalogus",
                        url="https://catalogus-2.nl/api/v1/catalogussen/111",
                        volgnummer=1,
                        informatieobjecttypen=informatieobjecttypen2,
                    ),
                ],
            },
        )
        m.get(
            "https://catalogus-2.nl/api/v1/informatieobjecttypen",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": informatieobjecttypen2,
            },
        )

    def test_must_be_logged_in_as_admin(self, m):
        user = UserFactory.create()
        url = reverse("api:zgw_apis:iotypen-list")
        self.client.force_login(user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_without_filter_param(self, m):
        user = StaffUserFactory.create()
        url = reverse("api:zgw_apis:iotypen-list")
        self.client.force_login(user)

        self.install_mocks(m)

        with patch(
            "openforms.registrations.contrib.zgw_apis.api.views.ZgwConfig.get_solo",
            return_value=ZgwConfig(default_zgw_api_group=self.zgw_group1),
        ):
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(len(data), 2)

    def test_retrieve_without_filter_param_no_default(self, m):
        user = StaffUserFactory.create()
        url = reverse("api:zgw_apis:iotypen-list")
        self.client.force_login(user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_retrieve_with_filter_params(self, m):
        user = StaffUserFactory.create()
        url = furl(reverse("api:zgw_apis:iotypen-list"))
        url.args["zgw_api_group"] = self.zgw_group2.pk
        url.args["registration_backend"] = "zgw-create-zaak"
        self.client.force_login(user)

        self.install_mocks(m)

        response = self.client.get(url.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(len(data), 1)

    def test_filter_with_invalid_param(self, m):
        user = StaffUserFactory.create()
        url = furl(reverse("api:zgw_apis:iotypen-list"))
        url.args["zgw_api_group"] = "INVALID"
        self.client.force_login(user)

        response = self.client.get(url.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_with_object_api(self, m):
        user = StaffUserFactory.create()
        url = furl(reverse("api:zgw_apis:iotypen-list"))
        url.args["registration_backend"] = "objects_api"
        self.client.force_login(user)

        self.install_mocks(m)

        with patch(
            "openforms.registrations.contrib.zgw_apis.api.views.ObjectsAPIConfig.get_solo",
            return_value=ObjectsAPIConfig(catalogi_service=self.zgw_group1.ztc_service),
        ):
            response = self.client.get(url.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(len(data), 2)
