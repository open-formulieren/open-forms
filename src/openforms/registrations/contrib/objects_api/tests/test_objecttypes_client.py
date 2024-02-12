from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openforms.utils.tests.vcr import OFVCRMixin

from ..client import get_objecttypes_client
from ..models import ObjectsAPIConfig


def get_test_config() -> ObjectsAPIConfig:
    """Returns a preconfigured ``ObjectsAPIConfig`` instance matching the docker compose configuration."""
    return ObjectsAPIConfig(
        objecttypes_service=Service(
            api_root="http://localhost:8001/api/v2/",
            api_type=APITypes.orc,
            oas="https://example.com/",
            header_key="Authorization",
            header_value="Token 171be5abaf41e7856b423ad513df1ef8f867ff48",
            auth_type=AuthTypes.api_key,
        )
    )


class ObjecttypesClientTest(OFVCRMixin, TestCase):

    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self) -> None:
        super().setUp()

        patcher = patch(
            "openforms.registrations.contrib.objects_api.client.ObjectsAPIConfig.get_solo",
            return_value=get_test_config(),
        )

        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_list_objecttypes(self):
        with get_objecttypes_client() as client:
            data = client.list_objecttypes()

        self.assertEqual(len(data), 2)

    def test_list_objectypes_pagination(self):
        with get_objecttypes_client() as client:
            data = client.list_objecttypes(page=1, page_size=1)

        self.assertEqual(len(data), 1)

    def test_list_objecttype_version(self):
        with get_objecttypes_client() as client:
            data = client.list_objecttype_versions(
                "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48"
            )

        self.assertEqual(len(data), 3)
