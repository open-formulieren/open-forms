from pathlib import Path

from django.test import TestCase, override_settings

from openforms.utils.tests.vcr import OFVCRMixin

from ..plugin import ZaakOptionsSerializer
from .factories import ZGWApiGroupConfigFactory

FILES_DIR = Path(__file__).parent / "files"


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

        cls.zgw_group = ZGWApiGroupConfigFactory.create(for_test_docker_compose=True)

    def test_no_zgw_api_group(self):
        # No zgw_api_group provided
        serializer = ZaakOptionsSerializer(
            data={
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
            }
        )

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("zgw_api_group", serializer.errors)

    def test_existing_provided_variable_in_specific_zaaktype(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "property_mappings": [
                {"component_key": "textField", "eigenschap": "a property name"}
            ],
        }
        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)
        self.assertNotIn("property_mappings", serializer.errors)

    def test_provided_variable_does_not_exist_in_specific_zaaktype(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
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
        data = {
            "zgw_api_group": self.zgw_group.pk,
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
        data = {
            "zgw_api_group": self.zgw_group.pk,
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

    def test_valid_omschrijving(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "medewerker_roltype": "Baliemedewerker",
        }

        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)

    @override_settings(LANGUAGE_CODE="en")
    def test_invalid_omschrijving(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "medewerker_roltype": "Absent roltype",
        }

        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("medewerker_roltype", serializer.errors)
        self.assertEqual(
            "Could not find a roltype with this description related to the zaaktype.",
            serializer.errors["medewerker_roltype"][0],
        )
