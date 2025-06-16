from pathlib import Path
from unittest.mock import patch

from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.utils.tests.vcr import OFVCRMixin

from ....registry import register

plugin = register["objects_api"]

VCR_TEST_FILES = Path(__file__).parent / "files"


class ObjectsAPIPrefillPluginConfigTests(OFVCRMixin, APITestCase):
    """This test case requires the Objects & Objecttypes API to be running.
    See the relevant Docker compose in the ``docker/`` folder.
    """

    VCR_TEST_FILES = VCR_TEST_FILES

    def setUp(self):
        super().setUp()

        config_patcher = patch(
            "openforms.registrations.contrib.objects_api.models.ObjectsAPIConfig.get_solo",
            return_value=ObjectsAPIConfig(),
        )
        self.mock_get_config = config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.objects_api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def test_invalid_service_raises_exception(self):
        objects_service = ServiceFactory.create(
            api_root="http://localhost:8002/api/v2/invalid",
            api_type=APITypes.orc,
            header_key="Authorization",
            header_value="Token INVALID",
            auth_type=AuthTypes.api_key,
        )
        self.objects_api_group.objects_service = objects_service
        self.objects_api_group.save()

        with self.assertRaises(
            InvalidPluginConfiguration,
        ) as exc:
            plugin.check_config()

        self.assertIn("404 Client Error", exc.exception.args[0])
