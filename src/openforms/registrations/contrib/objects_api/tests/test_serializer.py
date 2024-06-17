from pathlib import Path

from django.test import TestCase

from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.utils.tests.vcr import OFVCRMixin

from ..config import ObjectsAPIOptionsSerializer
from ..models import ObjectsAPIGroupConfig

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

        cls.objects_api_group = ObjectsAPIGroupConfig.objects.create(
            objecttypes_service=ServiceFactory.create(
                api_root="http://localhost:8001/api/v2/",
                api_type=APITypes.orc,
                oas="https://example.com/",
                header_key="Authorization",
                header_value="Token 171be5abaf41e7856b423ad513df1ef8f867ff48",
                auth_type=AuthTypes.api_key,
            ),
            objects_service=ServiceFactory.create(
                api_root="http://localhost:8002/api/v2/",
                api_type=APITypes.orc,
                oas="https://example.com/",
                header_key="Authorization",
                # See the docker compose fixtures:
                header_value="Token 7657474c3d75f56ae0abd0d1bf7994b09964dca9",
                auth_type=AuthTypes.api_key,
            ),
            drc_service=ServiceFactory.create(
                api_root="http://localhost:8003/documenten/api/v1/",
                api_type=APITypes.drc,
                # See the docker compose fixtures:
                client_id="test_client_id",
                secret="test_secret_key",
                auth_type=AuthTypes.zgw,
            ),
            catalogi_service=ServiceFactory.create(
                api_root="http://localhost:8003/catalogi/api/v1/",
                api_type=APITypes.ztc,
                # See the docker compose fixtures:
                client_id="test_client_id",
                secret="test_secret_key",
                auth_type=AuthTypes.zgw,
            ),
        )

    def test_invalid_fields_v1(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.pk,
                "version": 1,
                "objecttype": "https://objecttypen.nl/api/v2/objecttypes/2c77babf-a967-4057-9969-0200320d23f1",
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
                "objecttype": "https://objecttypen.nl/api/v2/objecttypes/2c77babf-a967-4057-9969-0200320d23f1",
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
                "objecttype": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
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
                "objecttype": "http://localhost:8001/api/v2/objecttypes/1",
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
                "objecttype": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 999,
            },
        )

        self.assertFalse(options.is_valid())
        self.assertIn("objecttype_version", options.errors)
        error = options.errors["objecttype_version"][0]
        self.assertEqual(error.code, "not-found")

    def test_valid_serializer(self):
        options = ObjectsAPIOptionsSerializer(
            data={
                "objects_api_group": self.objects_api_group.pk,
                "version": 2,
                "objecttype": "http://localhost:8001/api/v2/objecttypes/8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 1,
                "informatieobjecttype_attachment": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7a474713-0833-402a-8441-e467c08ac55b",
                "informatieobjecttype_submission_report": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/b2d83b94-9b9b-4e80-a82f-73ff993c62f3",
                "informatieobjecttype_submission_csv": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/531f6c1a-97f7-478c-85f0-67d2f23661c7",
            },
        )

        self.assertTrue(options.is_valid())
