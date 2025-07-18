from pathlib import Path

from django.test import TestCase

from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openforms.utils.tests.vcr import OFVCRMixin

from ..clients import get_objecttypes_client
from ..models import ObjectsAPIGroupConfig


class ObjecttypesClientTest(OFVCRMixin, TestCase):
    VCR_TEST_FILES = Path(__file__).parent / "files"

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.test_config = ObjectsAPIGroupConfig(
            objecttypes_service=Service(
                api_root="http://localhost:8001/api/v2/",
                api_type=APITypes.orc,
                header_key="Authorization",
                header_value="Token 171be5abaf41e7856b423ad513df1ef8f867ff48",
                auth_type=AuthTypes.api_key,
            )
        )

    def test_list_objecttypes(self):
        with get_objecttypes_client(self.test_config) as client:
            data = client.list_objecttypes()

        self.assertGreaterEqual(len(data), 4)

    def test_list_objectypes_pagination(self):
        with get_objecttypes_client(self.test_config) as client:
            data = client.list_objecttypes(page=1, page_size=1)

        self.assertEqual(len(data), 1)

    def test_list_objecttype_versions(self):
        with get_objecttypes_client(self.test_config) as client:
            data = client.list_objecttype_versions(
                "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"
            )

        self.assertEqual(len(data), 4)

    def test_get_objecttype_version(self):
        with get_objecttypes_client(self.test_config) as client:
            data = client.get_objecttype_version(
                "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                version=1,
            )
        self.assertEqual(data["version"], 1)
