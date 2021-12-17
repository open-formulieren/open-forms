import json
import os

from openforms.contrib.kvk.models import KVKConfig
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory


class KVKTestMixin:
    def load_json_mock(self, name):
        path = os.path.join(os.path.dirname(__file__), "files", name)
        with open(path, "r") as f:
            return json.load(f)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = KVKConfig.get_solo()
        config.service = ServiceFactory(
            api_root="https://companies/",
            oas="https://companies/api/schema/openapi.yaml",
        )
        config.profiles = ServiceFactory(
            api_root="https://hoofdvestiging/",
            oas="https://hoofdvestiging/schema/openapi.yaml",
        )
        config.save()
