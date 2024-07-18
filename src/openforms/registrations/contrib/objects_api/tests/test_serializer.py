from pathlib import Path

from django.test import TestCase

from openforms.utils.tests.vcr import OFVCRMixin

from ..config import ObjectsAPIOptionsSerializer
from .factories import ObjectsAPIGroupConfigFactory

FILES_DIR = Path(__file__).parent / "files"


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

    VCR_TEST_FILES = FILES_DIR

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

        # This group shouldn't be usable:
        cls.invalid_objects_api_group = ObjectsAPIGroupConfigFactory.create(
            objecttypes_service=None,
            drc_service=None,
            catalogi_service=None,
        )

    def test_invalid_fields_v1(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.pk,
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
                "objects_api_group": self.objects_api_group.pk,
                "version": 2,
                "objecttype": "2c77babf-a967-4057-9969-0200320d23f1",
                "objecttype_version": 1,
                "content_json": "dummy",
            },
            context={"validate_business_logic": False},
        )
        self.assertFalse(options.is_valid())

    def test_unknown_informatieobjecttype(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.pk,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/1",
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("informatieobjecttype_attachment", options.errors)
        error = options.errors["informatieobjecttype_attachment"][0]
        self.assertEqual(error.code, "not-found")

    def test_unknown_objecttype(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.pk,
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
                "objects_api_group": self.objects_api_group.pk,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 999,
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("objecttype_version", options.errors)
        error = options.errors["objecttype_version"][0]
        self.assertEqual(error.code, "not-found")

    def test_invalid_objects_api_group(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.invalid_objects_api_group.pk,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
                "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
                "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("objects_api_group", options.errors)
        error = options.errors["objects_api_group"][0]
        self.assertEqual(error.code, "does_not_exist")

    def test_valid_serializer(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.pk,
                "version": 2,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
                "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
                "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            },
        )

        self.assertTrue(options.is_valid())
