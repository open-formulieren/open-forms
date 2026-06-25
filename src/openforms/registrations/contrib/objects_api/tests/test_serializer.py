from django.test import TestCase

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..config import ObjectsAPIOptionsSerializer


class ObjectsAPIOptionsSerializerTest(OFVCRMixin, TestCase):
    """
    Test validation of the Objects API registration serializer.

    The VCR tests make use of the Open Zaak and Objects APIs Docker Compose.
    From the root of the repository run:

    .. codeblock:: bash

        cd docker
        docker compose -f docker-compose.objects-apis.yml up -d
        docker compose -f docker-compose.open-zaak.yml up -d

    See the relevant READMEs to load the necessary data into the instances.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def test_invalid_fields_v1(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 1,
                "objecttype": "2c77babf-a967-4057-9969-0200320d23f1",
                "objecttype_version": 1,
                "variables_mapping": [],
            },
            context={"validate_business_logic": False},
        )
        self.assertFalse(options.is_valid())

    def test_invalid_fields_v2(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "2c77babf-a967-4057-9969-0200320d23f1",
                "objecttype_version": 1,
                "content_json": "dummy",
            },
            context={"validate_business_logic": False},
        )
        self.assertFalse(options.is_valid())

    def test_unknown_objecttype(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                # Unknown UUID:
                "objecttype": "3064be01-87cd-45e1-8b57-904e183283d6",
                "objecttype_version": 1,
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("objecttype", options.errors)
        error = options.errors["objecttype"][0]
        self.assertEqual(error.code, "not-found")

    def test_unknown_objecttype_version(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 999,
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("objecttype_version", options.errors)
        error = options.errors["objecttype_version"][0]
        self.assertEqual(error.code, "not-found")

    def test_auth_attribute_path_required_if_update_existing_object_is_true(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "update_existing_object": True,
                "auth_attribute_path": [],
            },
        )

        result = options.is_valid()

        self.assertFalse(result)
        self.assertIn("auth_attribute_path", options.errors)
        error = options.errors["auth_attribute_path"][0]
        self.assertEqual(error.code, "required")

    def test_valid_serializer(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "catalogue": {
                    "domain": "TEST",
                    "rsin": "000000000",
                },
                "iot_attachment": "PDF Informatieobjecttype",
                "iot_submission_report": "CSV Informatieobjecttype",
                "iot_submission_csv": "Attachment Informatieobjecttype",
            },
        )

        self.assertTrue(options.is_valid())

    def test_catalogue_reference_badly_formatted_data(self):
        base = {
            "objects_api_group": self.objects_api_group.identifier,
            "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            "objecttype_version": 1,
        }

        with self.subTest("domain without rsin"):
            serializer = ObjectsAPIOptionsSerializer(
                data={**base, "catalogue": {"domain": "TEST"}},
            )

            valid = serializer.is_valid()

            self.assertFalse(valid)
            self.assertIn("catalogue", serializer.errors)
            error = serializer.errors["catalogue"]["non_field_errors"][0]
            self.assertIn("domain", error)
            self.assertIn("rsin", error)

        with self.subTest("rsin without domain"):
            serializer = ObjectsAPIOptionsSerializer(
                data={**base, "catalogue": {"rsin": "123456782"}}
            )

            valid = serializer.is_valid()

            self.assertFalse(valid)
            self.assertIn("catalogue", serializer.errors)
            error = serializer.errors["catalogue"]["non_field_errors"][0]
            self.assertIn("domain", error)
            self.assertIn("rsin", error)

        with self.subTest("invalid RSIN"):
            serializer = ObjectsAPIOptionsSerializer(
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
            "objects_api_group": self.objects_api_group.identifier,
            "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            "objecttype_version": 1,
        }

        with self.subTest("valid catalogue reference"):
            serializer1 = ObjectsAPIOptionsSerializer(
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
            serializer2 = ObjectsAPIOptionsSerializer(
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

    def test_validate_iot_descriptions_within_catalogue(self):
        api_group = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)

        for field in (
            "iot_submission_report",
            "iot_submission_csv",
            "iot_attachment",
        ):
            with self.subTest(
                "invalid reference", field=field, catalogue_ref="explicit"
            ):
                serializer = ObjectsAPIOptionsSerializer(
                    data={
                        "objects_api_group": api_group.identifier,
                        "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                        "catalogue": {
                            "domain": "OTHER",
                            "rsin": "000000000",
                        },
                        field: "PDF Informatieobjecttype",
                    }
                )

                valid = serializer.is_valid()

                self.assertFalse(valid)
                self.assertIn(field, serializer.errors)
                err = serializer.errors[field][0]
                self.assertEqual(err.code, "not-found")

            with self.subTest("valid reference", field=field, catalogue_ref="explicit"):
                serializer = ObjectsAPIOptionsSerializer(
                    data={
                        "objects_api_group": api_group.identifier,
                        "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                        "catalogue": {
                            "domain": "TEST",
                            "rsin": "000000000",
                        },
                        field: "PDF Informatieobjecttype",
                    }
                )

                valid = serializer.is_valid()

                self.assertTrue(valid)

    def test_iot_specified_but_catalogue_missing(self):
        api_group = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)

        cases = (
            {},
            {"catalogue": {}},
        )

        for case in cases:
            with self.subTest(catalogue=case):
                serializer = ObjectsAPIOptionsSerializer(
                    data={
                        "objects_api_group": api_group.identifier,
                        "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                        "iot_attachment": "PDF Informatieobjecttype",
                        **case,
                    }
                )

                valid = serializer.is_valid()

                self.assertFalse(valid)
                self.assertIn("catalogue", serializer.errors)
                err = serializer.errors["catalogue"][0]
                self.assertEqual(err.code, "required")

    def test_validate_iot_descriptions_in_file_options(self):
        # Note that we can't yet validate that the file keys point to actual file
        # components - backend options validation runs before the form definitions are
        # created/updated.
        api_group = ObjectsAPIGroupConfigFactory.create(for_test_docker_compose=True)
        base_data = {
            "objects_api_group": api_group.identifier,
            "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
            "objecttype_version": 1,
            "catalogue": {
                "domain": "TEST",
                "rsin": "000000000",
            },
            "iot_attachment": "Attachment Informatieobjecttype",
        }

        with self.subTest("valid reference"):
            serializer = ObjectsAPIOptionsSerializer(
                data={
                    **base_data,
                    "files": [
                        {
                            "key": "someFileComponent",
                            "document_type_description": "PDF Informatieobjecttype",
                        },
                        {
                            "key": "otherFileComponent",
                            "title": "Custom title",
                        },
                    ],
                }
            )

            valid = serializer.is_valid()

            self.assertTrue(valid)

        with self.subTest("invalid reference"):
            serializer = ObjectsAPIOptionsSerializer(
                data={
                    **base_data,
                    "files": [
                        {
                            "key": "someFileComponent",
                            "document_type_description": "33b4fc70",
                        }
                    ],
                }
            )

            valid = serializer.is_valid()

            self.assertFalse(valid)
            err = serializer.errors["files"][0]["document_type_description"]
            self.assertEqual(err.code, "not-found")
