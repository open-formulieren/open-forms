from pathlib import Path
from unittest.mock import patch

from zgw_consumers.constants import AuthTypes

from openforms.utils.tests.cache import clear_caches

from ....models import AppointmentsConfig
from ..models import QmaticConfig
from .factories import ServiceFactory

TESTS_DIR = Path(__file__).parent.resolve()
TEST_FILES = TESTS_DIR / "data"
MOCK_DIR = TESTS_DIR / "mock"


def mock_response(filename: str):
    full_path = MOCK_DIR / filename
    return full_path.read_text()


class MockConfigMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # type: ignore

        cls.service = ServiceFactory.create(auth_type=AuthTypes.no_auth)

    def setUp(self):
        super().setUp()  # type: ignore

        self.addCleanup(clear_caches)  # type: ignore

        main_config_patcher = patch(
            "openforms.appointments.utils.AppointmentsConfig.get_solo",
            return_value=AppointmentsConfig(plugin="qmatic"),
        )
        main_config_patcher.start()
        self.addCleanup(main_config_patcher.stop)  # type: ignore

        self.qmatic_config = QmaticConfig(service=self.service)
        self.api_root = self.qmatic_config.service.api_root
        qmatic_config_patchers = [
            patch(
                "openforms.appointments.contrib.qmatic.client.QmaticConfig.get_solo",
                return_value=self.qmatic_config,
            ),
            patch(
                "openforms.appointments.contrib.qmatic.plugin.QmaticConfig.get_solo",
                return_value=self.qmatic_config,
            ),
        ]
        for patcher in qmatic_config_patchers:
            patcher.start()
            self.addCleanup(patcher.stop)  # type: ignore
