from pathlib import Path
from unittest.mock import patch

from zgw_consumers.constants import APITypes, AuthTypes

from openforms.contrib.brk.models import BRKConfig
from zgw_consumers_ext.tests.factories import ServiceFactory

TEST_FILES = Path(__file__).parent.resolve() / "files"


BRK_SERVICE = ServiceFactory.build(
    api_root="https://api.brk.kadaster.nl/esd-eto-apikey/bevragen/v2/",
    oas="https://api.brk.kadaster.nl/esd-eto-apikey/bevragen/v2/",  # ignored/unused
    api_type=APITypes.orc,
    auth_type=AuthTypes.api_key,
    header_key="X-Api-Key",
    header_value="fake_changeme_when_testing",
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
