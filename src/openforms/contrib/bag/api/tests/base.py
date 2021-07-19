import json
import os

from openforms.contrib.bag.models import BAGConfig
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory


class BagTestMixin:
    def load_json_mock(self, name):
        path = os.path.join(os.path.dirname(__file__), "files", name)
        with open(path, "r") as f:
            return json.load(f)

    def load_binary_mock(self, name):
        path = os.path.join(os.path.dirname(__file__), "files", name)
        with open(path, "rb") as f:
            return f.read()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = BAGConfig.get_solo()
        service = ServiceFactory(
            api_root="https://bag/api/",
            oas="https://bag/api/schema/openapi.yaml",
        )
        config.bag_service = service
        config.save()
