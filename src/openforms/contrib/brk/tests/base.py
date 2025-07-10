import os
from pathlib import Path
from unittest.mock import patch

from maykin_common.vcr import _VCRTestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.brk.models import BRKConfig

TEST_FILES = Path(__file__).parent.resolve() / "files"
BRK_API_KEY = os.getenv("BRK_API_KEY", "placeholder_key")

BRK_SERVICE = ServiceFactory.build(
    api_root="https://api.brk.kadaster.nl/esd-eto-apikey/bevragen/v2/",
    api_type=APITypes.orc,
    auth_type=AuthTypes.api_key,
    header_key="X-Api-Key",
    header_value=BRK_API_KEY,
)

INVALID_BRK_SERVICE = ServiceFactory.build(
    api_root="https://api.brk.kadaster.nl/invalid",
    api_type=APITypes.orc,
    auth_type=AuthTypes.api_key,
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

    def _get_vcr_kwargs(self: _VCRTestCase, **kwargs):
        kwargs = super()._get_vcr_kwargs(**kwargs)
        kwargs["filter_headers"] = ["X-Api-Key"]
        return kwargs
