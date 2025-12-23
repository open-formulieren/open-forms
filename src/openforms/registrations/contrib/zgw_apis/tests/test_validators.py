from django.test import TestCase, override_settings

from typing_extensions import deprecated

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..plugin import ZaakOptionsSerializer
from .factories import ZGWApiGroupConfigFactory


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

    @deprecated("Legacy zaaktype URL")
    def test_bad_case_type_document_type_api_roots(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": "https://other-host.local/api/v1/zt/123",
            "informatieobjecttype": "https://other-host.local/api/v1/iot/456",
            "objects_api_group": None,
        }
        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("zaaktype", serializer.errors)
        self.assertIn("informatieobjecttype", serializer.errors)

    @deprecated("Legacy zaaktype URL")
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
            "objects_api_group": None,
        }
        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)
        self.assertNotIn("property_mappings", serializer.errors)

    def test_property_mappings_validated_against_case_type_identification(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "property_mappings": [
                {"component_key": "textField", "eigenschap": "a property name"},
                {"component_key": "textField", "eigenschap": "wrong property name"},
            ],
            "objects_api_group": None,
        }
        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("property_mappings", serializer.errors)
        self.assertNotIn(0, serializer.errors["property_mappings"])
        self.assertIn(1, serializer.errors["property_mappings"])
        self.assertIn("eigenschap", serializer.errors["property_mappings"][1])
        error = serializer.errors["property_mappings"][1]["eigenschap"]
        self.assertEqual(error.code, "not-found")

    @deprecated("Legacy zaaktype URL")
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
            "objects_api_group": None,
        }
        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("property_mappings", serializer.errors)
        self.assertIn(0, serializer.errors["property_mappings"])
        self.assertIn("eigenschap", serializer.errors["property_mappings"][0])

        error_msg = serializer.errors["property_mappings"][0]["eigenschap"]
        self.assertEqual(
            error_msg,
            "Could not find a property with the name 'wrong variable' in the case type",
        )

    @deprecated("Legacy zaaktype URL")
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
            "objects_api_group": None,
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
            "objects_api_group": None,
        }
        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("informatieobjecttype", serializer.errors)
        error = serializer.errors["informatieobjecttype"][0]
        self.assertEqual(error.code, "not-found")

    @deprecated("Legacy zaaktype URL")
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
            "objects_api_group": None,
        }

        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertTrue(is_valid)

    @deprecated("Legacy zaaktype URL")
    @override_settings(LANGUAGE_CODE="en")
    def test_invalid_roltype_omschrijving(self):
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
            "partners_roltype": "Invalid partners roltype",
            "children_roltype": "Invalid children roltype",
            "objects_api_group": None,
        }

        serializer = ZaakOptionsSerializer(data=data)
        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("medewerker_roltype", serializer.errors)
        self.assertIn("partners_roltype", serializer.errors)
        self.assertIn("children_roltype", serializer.errors)
        self.assertEqual(
            "Could not find a roltype with this description related to the zaaktype.",
            serializer.errors["medewerker_roltype"][0],
        )
        self.assertEqual(
            "Could not find a roltype with this description related to the zaaktype.",
            serializer.errors["partners_roltype"][0],
        )
        self.assertEqual(
            "Could not find a roltype with this description related to the zaaktype.",
            serializer.errors["children_roltype"][0],
        )

    def test_roltype_omschrijving_validated_against_case_type_identification(
        self,
    ):
        base = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "PARTN",
                "rsin": "000000000",
            },
            "case_type_identification": "ZAAKTYPE-2020-0000000001",
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/d2ea38b1-5215-402f-a3f5-2977d112bf72"
            ),
            "objects_api_group": None,
            "partners_description": "",
            "children_desription": "",
        }

        with self.subTest("medewerker:yes, partners:yes, children:yes"):
            data = {
                **base,
                "catalogue": {
                    "domain": "CHILD",
                    "rsin": "000000000",
                },
                "case_type_identification": "ZAAKTYPE-2020-0000000002",
                "informatieobjecttype": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "informatieobjecttypen/68ce2d9c-fe0f-49cc-a1d6-ddb3d404da35"
                ),
                "medewerker_roltype": "Children role type",
                "partners_roltype": "Children role type",
                "children_roltype": "Children role type",
            }
            serializer = ZaakOptionsSerializer(data=data)
            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("medewerker:no, partners:no, children:no"):
            serializer = ZaakOptionsSerializer(data=base)
            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("medewerker:yes, partners:no, children:no"):
            data = {**base, "medewerker_roltype": "Partner role type"}
            serializer = ZaakOptionsSerializer(data=data)
            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("medewerker:no, partners:yes, children:no"):
            data = {**base, "partners_roltype": "Partner role type"}
            serializer = ZaakOptionsSerializer(data=data)
            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("medewerker:no, partners:no, children:yes"):
            data = {
                **base,
                "catalogue": {
                    "domain": "CHILD",
                    "rsin": "000000000",
                },
                "case_type_identification": "ZAAKTYPE-2020-0000000002",
                "informatieobjecttype": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "informatieobjecttypen/68ce2d9c-fe0f-49cc-a1d6-ddb3d404da35"
                ),
                "children_roltype": "Children role type",
            }
            serializer = ZaakOptionsSerializer(data=data)
            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("medewerker:yes, partners:yes, children:no"):
            data = {
                **base,
                "medewerker_roltype": "Partner role type",
                "partners_roltype": "Partner role type",
            }
            serializer = ZaakOptionsSerializer(data=data)
            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("invalid roltype"):
            data = {
                **base,
                "medewerker_roltype": "Invalid roltype",
                "partners_roltype": "Invalid roltype",
                "children_roltype": "Invalid roltype",
            }
            serializer = ZaakOptionsSerializer(data=data)
            is_valid = serializer.is_valid()

            self.assertFalse(is_valid)
            self.assertIn("medewerker_roltype", serializer.errors)
            self.assertIn("partners_roltype", serializer.errors)
            self.assertIn("children_roltype", serializer.errors)
            self.assertEqual(
                "Could not find a roltype with this description related to the zaaktype.",
                serializer.errors["medewerker_roltype"][0],
            )
            self.assertEqual(
                "Could not find a roltype with this description related to the zaaktype.",
                serializer.errors["partners_roltype"][0],
            )
            self.assertEqual(
                "Could not find a roltype with this description related to the zaaktype.",
                serializer.errors["children_roltype"][0],
            )

    def test_medewerker_roltype_omschrijving_validated_against_case_type_identification(
        self,
    ):
        base = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "objects_api_group": None,
        }

        with self.subTest("valid"):
            data = {**base, "medewerker_roltype": "Baliemedewerker"}
            serializer = ZaakOptionsSerializer(data=data)

            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("invalid"):
            data = {**base, "medewerker_roltype": "Absent roltype"}
            serializer = ZaakOptionsSerializer(data=data)

            is_valid = serializer.is_valid()

            self.assertFalse(is_valid)
            self.assertIn("medewerker_roltype", serializer.errors)
            self.assertEqual(
                "Could not find a roltype with this description related to the zaaktype.",
                serializer.errors["medewerker_roltype"][0],
            )

    def test_catalogue_reference_badly_formatted_data(self):
        base = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
        }

        with self.subTest("domain without rsin"):
            serializer = ZaakOptionsSerializer(
                data={**base, "catalogue": {"domain": "TEST"}},
            )

            valid = serializer.is_valid()

            self.assertFalse(valid)
            self.assertIn("catalogue", serializer.errors)
            error = serializer.errors["catalogue"]["non_field_errors"][0]
            self.assertIn("domain", error)
            self.assertIn("rsin", error)

        with self.subTest("rsin without domain"):
            serializer = ZaakOptionsSerializer(
                data={**base, "catalogue": {"rsin": "123456782"}}
            )

            valid = serializer.is_valid()

            self.assertFalse(valid)
            self.assertIn("catalogue", serializer.errors)
            error = serializer.errors["catalogue"]["non_field_errors"][0]
            self.assertIn("domain", error)
            self.assertIn("rsin", error)

        with self.subTest("invalid RSIN"):
            serializer = ZaakOptionsSerializer(
                data={
                    "catalogue": {
                        "domain": "ok",
                        "rsin": "AAAAAAAAA",
                    }
                }
            )

            valid = serializer.is_valid()

            self.assertFalse(valid)
            self.assertIn("catalogue", serializer.errors)
            self.assertIn("rsin", serializer.errors["catalogue"])

    def test_catalogue_reference_with_api_calls(self):
        base = {
            "zgw_api_group": self.zgw_group.pk,
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "objects_api_group": None,
        }

        with self.subTest("valid catalogue reference"):
            serializer1 = ZaakOptionsSerializer(
                data={
                    **base,
                    "catalogue": {
                        "domain": "TEST",
                        "rsin": "000000000",
                    },
                }
            )

            valid1 = serializer1.is_valid()

            self.assertTrue(valid1)

        with self.subTest("invalid catalogus reference"):
            serializer2 = ZaakOptionsSerializer(
                data={
                    **base,
                    "catalogue": {
                        "domain": "NOOPE",
                        "rsin": "000000000",
                    },
                }
            )

            valid2 = serializer2.is_valid()

            self.assertFalse(valid2)
            self.assertIn("catalogue", serializer2.errors)
            err = serializer2.errors["catalogue"][0]
            self.assertEqual(err.code, "invalid-catalogue")

    def test_validation_case_type_document_type_in_catalogue(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            # Bad UUIDs, they don't exist in the API, so they're definitely not members
            # of the catalogue resource
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/111111111-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/111111111-97f7-478c-85f0-67d2f23661c7"
            ),
            "objects_api_group": None,
        }
        serializer = ZaakOptionsSerializer(data=data)

        result = serializer.is_valid()

        self.assertFalse(result)
        self.assertIn("zaaktype", serializer.errors)
        err = serializer.errors["zaaktype"][0]
        self.assertEqual(err.code, "not-found")
        self.assertIn("informatieobjecttype", serializer.errors)
        err = serializer.errors["informatieobjecttype"][0]
        self.assertEqual(err.code, "not-found")

    def test_case_type_identification_or_zaaktype_url_required(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "objects_api_group": None,
        }
        serializer = ZaakOptionsSerializer(data=data)

        result = serializer.is_valid()

        self.assertFalse(result)
        self.assertIn("case_type_identification", serializer.errors)
        err = serializer.errors["case_type_identification"][0]
        self.assertEqual(err.code, "required")

    def test_catalogue_required_when_case_type_identification_provided(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "case_type_identification": "ZT-001",
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "objects_api_group": None,
        }
        serializer = ZaakOptionsSerializer(data=data)

        result = serializer.is_valid()

        self.assertFalse(result)
        self.assertIn("catalogue", serializer.errors)
        err = serializer.errors["catalogue"][0]
        self.assertEqual(err.code, "required")

    def test_validate_case_type_exists_when_case_type_identification_is_provided(self):
        base = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "objects_api_group": None,
        }

        with self.subTest("case type exists"):
            data = {
                **base,
                "case_type_identification": "ZT-001",
            }
            serializer = ZaakOptionsSerializer(data=data)

            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("case type does not exist"):
            data = {
                **base,
                "case_type_identification": "i-am-a-bad-reference",
            }
            serializer = ZaakOptionsSerializer(data=data)

            is_valid = serializer.is_valid()

            self.assertFalse(is_valid)
            self.assertIn("case_type_identification", serializer.errors)
            err = serializer.errors["case_type_identification"][0]
            self.assertEqual(err.code, "not-found")

    def test_validation_objects_api_group_not_null_if_objecttype_is_defined(self):
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "objects_api_group": None,
            "objecttype": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
        }
        serializer = ZaakOptionsSerializer(data=data)

        result = serializer.is_valid()

        self.assertFalse(result)
        self.assertIn("objects_api_group", serializer.errors)
        err = serializer.errors["objects_api_group"][0]
        self.assertEqual(err.code, "required")

    def test_validation_objecttype_api_root_must_match_objecttypes_service_api_root(
        self,
    ):
        objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
        )
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "zaaktype": (
                "http://localhost:8003/catalogi/api/v1/"
                "zaaktypen/1f41885e-23fc-4462-bbc8-80be4ae484dc"
            ),
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7"
            ),
            "objects_api_group": objects_api_group.identifier,
            "objecttype": "http://incorrect.domain/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
        }
        serializer = ZaakOptionsSerializer(data=data)

        result = serializer.is_valid()

        self.assertFalse(result)
        self.assertIn("objecttype", serializer.errors)
        err = serializer.errors["objecttype"][0]
        self.assertEqual(err.code, "invalid")

    def test_document_type_must_be_provided(self):
        # either informatieobjecttype or document_type_description must be provided
        data = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
        }
        serializer = ZaakOptionsSerializer(data=data)

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)
        self.assertIn("document_type_description", serializer.errors)
        err = serializer.errors["document_type_description"][0]
        self.assertEqual(err.code, "required")

    def test_validate_document_type_exists_when_description_is_provided(self):
        base = {
            "zgw_api_group": self.zgw_group.pk,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "case_type_identification": "ZT-001",
        }

        with self.subTest("document type exists"):
            data = {
                **base,
                "document_type_description": "Attachment Informatieobjecttype",
            }
            serializer = ZaakOptionsSerializer(data=data)

            is_valid = serializer.is_valid()

            self.assertTrue(is_valid)

        with self.subTest("document type exists, not related to case type"):
            data = {
                **base,
                "document_type_description": "PDF Informatieobjecttype",
            }
            serializer = ZaakOptionsSerializer(data=data)

            is_valid = serializer.is_valid()

            self.assertFalse(is_valid)
            self.assertIn("document_type_description", serializer.errors)
            err = serializer.errors["document_type_description"][0]
            self.assertEqual(err.code, "not-found")

        with self.subTest("document type does not exist"):
            data = {
                **base,
                "document_type_description": "i-do-not-exist",
            }
            serializer = ZaakOptionsSerializer(data=data)

            is_valid = serializer.is_valid()

            self.assertFalse(is_valid)
            self.assertIn("document_type_description", serializer.errors)
            err = serializer.errors["document_type_description"][0]
            self.assertEqual(err.code, "not-found")
