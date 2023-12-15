import json
from pathlib import Path
from typing import Literal
from unittest.mock import patch

from zgw_consumers.constants import APITypes, AuthTypes

from openforms.contrib.brk.models import BRKConfig
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


BRK_SERVICE = ServiceFactory.build(
    api_root="http://localhost:8150/",
    oas="http://localhost:8150/",  # ignored/unused
    api_type=APITypes.orc,
    auth_type=AuthTypes.api_key,
    header_key="apikey",
    header_value="l7xx1f2691f2520d487b902f4e0b57a0b197",
)


class BRKTestMixin:

    api_root = BRK_SERVICE.api_root

    def setUp(self):
        super().setUp()

        patcher = patch(
            "openforms.contrib.brk.client.BRKConfig.get_solo",
            return_value=BRKConfig(service=BRK_SERVICE),
        )
        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)