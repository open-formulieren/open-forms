from pathlib import Path
from unittest.mock import patch

from openforms.utils.tests.cache import clear_caches

from ....models import AppointmentsConfig
from ..models import QmaticConfig
from .factories import ServiceFactory

MOCK_DIR = Path(__file__).parent.resolve() / "mock"


def mock_response(filename: str):
    full_path = MOCK_DIR / filename
    return full_path.read_text()


class MockConfigMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # type: ignore

        cls.service = ServiceFactory.create()

    def setUp(self):
        super().setUp()  # type: ignore

        self.addCleanup(clear_caches)  # type: ignore

        main_config_patcher = patch(
            "openforms.appointments.utils.AppointmentsConfig.get_solo",
            return_value=AppointmentsConfig(plugin="qmatic"),
        )
        main_config_patcher.start()
        self.addCleanup(main_config_patcher.stop)  # type: ignore

        qmatic_config = QmaticConfig(service=self.service)
        self.api_root = qmatic_config.service.api_root
        jcc_config_patcher = patch(
            "openforms.appointments.contrib.qmatic.client.QmaticConfig.get_solo",
            return_value=qmatic_config,
        )
        jcc_config_patcher.start()
        self.addCleanup(jcc_config_patcher.stop)  # type: ignore
