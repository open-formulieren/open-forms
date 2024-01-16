from unittest.mock import patch

from django.test import TestCase, override_settings

import requests_mock
from zgw_consumers.test import generate_oas_component

from ..models import ZgwConfig
from ..plugin import ZaakOptionsSerializer
from .factories import ZGWApiGroupConfigFactory


@requests_mock.Mocker()
class OmschrijvingValidatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )

    def test_valid_omschrijving(self, m):
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
        self.assertIn("medewerker_roltype", serializer.errors)
        self.assertEqual(
            "Could not find a roltype with this description related to the zaaktype.",
            serializer.errors["medewerker_roltype"][0],
        )


@override_settings(LANGUAGE_CODE="en")
class ZGWAPIGroupConfigTest(TestCase):
    def test_no_zgw_api_group_and_no_default(self):
        # No zgw_api_group provided
        serializer = ZaakOptionsSerializer(data={})

        # No ZgwConfig.default_zgw_api_group configured
        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZgwConfig.get_solo",
            return_value=ZgwConfig(),
        ):
            is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("zgw_api_group", serializer.errors)
        self.assertEqual(
            "No ZGW API set was configured on the form and no default was specified globally.",
            serializer.errors["zgw_api_group"][0],
        )

    def test_provided_variable_with_missing_eigenshap(self):
        zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )

        data = {
            "zgw_api_group": zgw_group.pk,
            "variables_properties": [{"component_key": "textField", "eigenshap": ""}],
        }
        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("variables_properties", serializer.errors)
        self.assertEqual(
            "Both variable selection and property name are required.",
            serializer.errors["variables_properties"][0],
        )
