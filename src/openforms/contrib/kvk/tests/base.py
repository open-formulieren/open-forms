import json
from pathlib import Path
from typing import Literal
from unittest.mock import patch

from zgw_consumers.constants import APITypes, AuthTypes

from openforms.contrib.kvk.models import KVKConfig
from zgw_consumers_ext.tests.factories import ServiceFactory

TEST_FILES = Path(__file__).parent.resolve() / "files"

TestFileNames = Literal[
    "basisprofiel_response.json",
    "basisprofiel_response_vve.json",
    "zoeken_response.json",
]


def load_json_mock(name: TestFileNames):
    with (TEST_FILES / name).open("r") as f:
        return json.load(f)


# See https://developers.kvk.nl/documentation/testing
KVK_SERVICE = ServiceFactory.build(
    api_root="https://api.kvk.nl/test/api/",
    oas="https://api.kvk.nl/test/api/",  # ignored/unused
    api_type=APITypes.orc,
    auth_type=AuthTypes.api_key,
    header_key="apikey",
    header_value="l7xx1f2691f2520d487b902f4e0b57a0b197",
)


class KVKTestMixin:

    api_root = KVK_SERVICE.api_root

    def setUp(self):
        super().setUp()

        patcher = patch(
            "openforms.contrib.kvk.client.KVKConfig.get_solo",
            return_value=KVKConfig(service=KVK_SERVICE),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
