from django.test import TestCase, override_settings

import requests_mock
from zds_client.oas import schema_fetcher
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.schema_mock import mock_service_oas_get

from ..plugin import ZaakOptionsSerializer
from .factories import ZGWApiGroupConfigFactory


@requests_mock.Mocker()
class OmschrijvingValidatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            zrc_service__oas="https://zaken.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten.nl/api/v1/",
            drc_service__oas="https://documenten.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
            ztc_service__oas="https://catalogus.nl/api/v1/schema/openapi.yaml",
        )

    def setUp(self):
        super().setUp()
        # reset cache to keep request_history indexes consistent
        schema_fetcher.cache.clear()
        self.addCleanup(schema_fetcher.cache.clear)

    def test_valid_omschrijving(self, m):
        mock_service_oas_get(m, "https://catalogus.nl/api/v1/", "catalogi")
        m.get(
            "https://catalogus.nl/api/v1/roltypen?zaaktype=https://catalogus.nl/api/v1/zaaktypen/111",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/RolType",
                        url="https://catalogus.nl/api/v1/roltypen/111",
                        omschrijving="Some description",
                    )
                ],
            },
        )

        data = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": "https://catalogus.nl/api/v1/zaaktypen/111",
            "medewerker_roltype": "Some description",
        }

        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)

    @override_settings(LANGUAGE_CODE="en")
    def test_invalid_omschrijving(self, m):
        mock_service_oas_get(m, "https://catalogus.nl/api/v1/", "catalogi")
        m.get(
            "https://catalogus.nl/api/v1/roltypen?zaaktype=https://catalogus.nl/api/v1/zaaktypen/111",
            status_code=200,
            json={
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            },
        )

        data = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": "https://catalogus.nl/api/v1/zaaktypen/111",
            "medewerker_roltype": "Some description",
        }

        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            "Could not find a roltype with this description related to the zaaktype",
            serializer.errors["non_field_errors"][0],
        )
