from unittest.mock import PropertyMock, patch

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

    @patch(
        "openforms.contrib.zgw.clients.catalogi.CatalogiClient.api_version",
        return_value=(1, 2, 0),
        new_callable=PropertyMock,
    )
    def test_unknown_informatieobjecttype(self, mock_api_version):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "informatieobjecttype_attachment": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "informatieobjecttypen/5e48c3a3-9b12-4692-98ee-5c4576b13465"
                ),
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("informatieobjecttype_attachment", options.errors)
        error = options.errors["informatieobjecttype_attachment"][0]
        self.assertEqual(error.code, "not-found")

    @patch(
        "openforms.contrib.zgw.clients.catalogi.CatalogiClient.api_version",
        return_value=(1, 0, 0),
        new_callable=PropertyMock,
    )
    def test_unknown_informatieobjecttype_validate_with_get_request(
        self, mock_api_version
    ):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "informatieobjecttype_attachment": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "informatieobjecttypen/5e48c3a3-9b12-4692-98ee-5c4576b13465"
                ),
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("informatieobjecttype_attachment", options.errors)
        error = options.errors["informatieobjecttype_attachment"][0]
        self.assertEqual(error.code, "not-found")

    def test_using_zaaktype_instead_of_informatieobjecttype(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.identifier,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "informatieobjecttype_attachment": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "zaaktypen/5e48c3a3-9b12-4692-98ee-5c4576b13465"  # incorrect endpoint
                ),
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("informatieobjecttype_attachment", options.errors)
        error = options.errors["informatieobjecttype_attachment"][0]
        self.assertEqual(error.code, "not-found")

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
                "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
                "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
                "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
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

    def test_validate_iot_urls_within_catalogue_implicit_catalogue_reference(self):
        # if no catalogue is referenced in the serializer options, the one from the api
        # group must be used if it's specified.
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
        )

        for field in (
            "informatieobjecttype_submission_report",
            "informatieobjecttype_submission_csv",
            "informatieobjecttype_attachment",
        ):
            with self.subTest(
                "invalid reference", field=field, catalogue_ref="implicit"
            ):
                serializer = ObjectsAPIOptionsSerializer(
                    data={
                        "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                        "objects_api_group": api_group.identifier,
                        field: (
                            f"{api_group.catalogi_service.api_root}informatieobjecttypen/"
                            "d1cfb1d8-8593-4814-919d-72e38e80388f"  # part of catalogue OTHER
                        ),
                    }
                )

                valid = serializer.is_valid()

                self.assertFalse(valid)
                self.assertIn(field, serializer.errors)
                err = serializer.errors[field][0]
                self.assertEqual(err.code, "not-found")

            with self.subTest("valid reference", field=field, catalogue_ref="implicit"):
                serializer = ObjectsAPIOptionsSerializer(
                    data={
                        "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                        "objects_api_group": api_group.identifier,
                        field: (
                            f"{api_group.catalogi_service.api_root}informatieobjecttypen/"
                            "29b63e5c-3835-4f68-8fad-f2aea9ae6b71"  # part of catalogue TEST
                        ),
                    }
                )

                valid = serializer.is_valid()

                self.assertTrue(valid)

        # check validation with explicit catalogue reference
        api_group2 = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )

        with self.subTest("invalid reference", catalogue_ref="explicit"):
            serializer = ObjectsAPIOptionsSerializer(
                data={
                    "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                    "objecttype_version": 1,
                    "objects_api_group": api_group2.identifier,
                    "catalogue": {
                        "domain": "TEST",
                        "rsin": "000000000",
                    },
                    "informatieobjecttype_attachment": (
                        f"{api_group2.catalogi_service.api_root}informatieobjecttypen/"
                        "d1cfb1d8-8593-4814-919d-72e38e80388f"  # part of catalogue OTHER
                    ),
                }
            )

            valid = serializer.is_valid()

            self.assertFalse(valid)
            self.assertIn("informatieobjecttype_attachment", serializer.errors)
            err = serializer.errors["informatieobjecttype_attachment"][0]
            self.assertEqual(err.code, "not-found")

        with self.subTest("valid reference", catalogue_ref="explicit"):
            serializer = ObjectsAPIOptionsSerializer(
                data={
                    "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                    "objecttype_version": 1,
                    "objects_api_group": api_group2.identifier,
                    "catalogue": {
                        "domain": "OTHER",
                        "rsin": "000000000",
                    },
                    "informatieobjecttype_submission_report": (
                        f"{api_group2.catalogi_service.api_root}informatieobjecttypen/"
                        "d1cfb1d8-8593-4814-919d-72e38e80388f"  # part of catalogue OTHER
                    ),
                }
            )

            valid = serializer.is_valid()

            self.assertTrue(valid)

    def test_validate_iot_descriptions_within_catalogue(self):
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="TEST",
            catalogue_rsin="000000000",
        )

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

            with self.subTest(
                "invalid reference", field=field, catalogue_ref="implicit"
            ):
                serializer = ObjectsAPIOptionsSerializer(
                    data={
                        "objects_api_group": api_group.identifier,
                        "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                        field: "Attachment Informatieobjecttype other catalog",
                    }
                )

                valid = serializer.is_valid()

                self.assertFalse(valid)
                self.assertIn(field, serializer.errors)
                err = serializer.errors[field][0]
                self.assertEqual(err.code, "not-found")

            with self.subTest("valid reference", field=field, catalogue_ref="implicit"):
                serializer = ObjectsAPIOptionsSerializer(
                    data={
                        "objects_api_group": api_group.identifier,
                        "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                        "objecttype_version": 1,
                        field: "PDF Informatieobjecttype",
                    }
                )

                valid = serializer.is_valid()

                self.assertTrue(valid)

    def test_iot_specified_but_catalogue_missing(self):
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )

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
