from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings

import requests_mock
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test import generate_oas_component
from zgw_consumers.test.factories import ServiceFactory

from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ZgwConfig
from ..plugin import ZaakOptionsSerializer
from .factories import ZGWApiGroupConfigFactory

FILES_DIR = Path(__file__).parent / "files"


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
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
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
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
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
class OptionsSerializerTests(OFVCRMixin, TestCase):
    """
    Test validations against ZGW API's.

    The VCR tests make use of the Open Zaak docker-compose, from the root of the
    repository run:

    .. codeblock:: bash

        cd docker
        docker compose -f docker-compose.open-zaak.yml up

    See the relevant README to load the necessary data into the instance.
    """

    VCR_TEST_FILES = FILES_DIR

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # create services for the docker-compose Open Zaak instance.
        _credentials = {
            "auth_type": AuthTypes.zgw,
            "client_id": "test_client_id",
            "secret": "test_secret_key",
        }
        cls.zaken_service = ServiceFactory.create(
            api_root="http://localhost:8003/zaken/api/v1/",
            api_type=APITypes.zrc,
            **_credentials,
        )
        cls.documenten_service = ServiceFactory.create(
            api_root="http://localhost:8003/documenten/api/v1/",
            api_type=APITypes.drc,
            **_credentials,
        )
        cls.catalogi_service = ServiceFactory.create(
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            **_credentials,
        )

    def test_no_zgw_api_group_and_no_default(self):
        # No zgw_api_group provided
        serializer = ZaakOptionsSerializer(
            data={
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            }
        )

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

    @requests_mock.Mocker()
    def test_existing_provided_variable_in_specific_zaaktype(self, m):
        zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )
        m.get(
            "https://catalogus.nl/api/v1/eigenschappen?zaaktype=https%3A%2F%2Fzaken.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://test.openzaak.nl/catalogi/api/v1/eigenschappen/1",
                        naam="a property name",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "10",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                ],
            },
        )

        data = {
            "zgw_api_group": zgw_group.pk,
            "zaaktype": "https://zaken.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "property_mappings": [
                {"component_key": "textField", "eigenschap": "a property name"}
            ],
        }
        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)
        self.assertNotIn("property_mappings", serializer.errors)

    @requests_mock.Mocker()
    def test_provided_variable_does_not_exist_in_specific_zaaktype(self, m):
        zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.nl/api/v1/",
            drc_service__api_root="https://documenten.nl/api/v1/",
            ztc_service__api_root="https://catalogus.nl/api/v1/",
        )
        m.get(
            "https://catalogus.nl/api/v1/eigenschappen?zaaktype=https%3A%2F%2Fzaken.nl%2Fapi%2Fv1%2Fzaaktypen%2F1",
            status_code=200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    generate_oas_component(
                        "catalogi",
                        "schemas/Eigenschap",
                        url="https://test.openzaak.nl/catalogi/api/v1/eigenschappen/1",
                        naam="a property name",
                        definitie="a definition",
                        specificatie={
                            "groep": "",
                            "formaat": "tekst",
                            "lengte": "10",
                            "kardinaliteit": "1",
                            "waardenverzameling": [],
                        },
                        toelichting="",
                        zaaktype="https://zaken.nl/api/v1/zaaktypen/1",
                    ),
                ],
            },
        )

        data = {
            "zgw_api_group": zgw_group.pk,
            "zaaktype": "https://zaken.nl/api/v1/zaaktypen/1",
            "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            "property_mappings": [
                {"component_key": "textField", "eigenschap": "wrong variable"}
            ],
        }
        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("property_mappings", serializer.errors)
        self.assertEqual(
            "Could not find a property with the name 'wrong variable' related to the zaaktype.",
            serializer.errors["property_mappings"][0],
        )

    def test_validate_zaaktype_within_configured_ztc_service(self):
        zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service=self.zaken_service,
            drc_service=self.documenten_service,
            ztc_service=self.catalogi_service,
        )
        data = {
            "zgw_api_group": zgw_group.pk,
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/ca5ffa84-3806-4663-a226-f2d163b79643"  # bad UUID
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
        }
        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("zaaktype", serializer.errors)
        error = serializer.errors["zaaktype"][0]
        self.assertEqual(error.code, "not-found")

    def test_validate_informatieobjecttype_within_configured_ztc_service(self):
        zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service=self.zaken_service,
            drc_service=self.documenten_service,
            ztc_service=self.catalogi_service,
        )
        data = {
            "zgw_api_group": zgw_group.pk,
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/ca5ffa84-3806-4663-a226-f2d163b79643"  # bad UUID
            ),
        }
        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("informatieobjecttype", serializer.errors)
        error = serializer.errors["informatieobjecttype"][0]
        self.assertEqual(error.code, "not-found")
