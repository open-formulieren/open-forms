from pathlib import Path
from unittest.mock import patch

from openforms.utils.tests.cache import clear_caches
from stuf.tests.factories import SoapServiceFactory

from ....models import AppointmentsConfig
from ..models import JccConfig

MOCK_DIR = Path(__file__).parent.resolve() / "mock"


def mock_response(filename: str):
    full_path = MOCK_DIR / filename
    return full_path.read_text()


class MockConfigMixin:
    extra_appointments_config = {}

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # type: ignore

        wsdl = str(MOCK_DIR / "GenericGuidanceSystem2.wsdl")
        cls.soap_service = SoapServiceFactory.create(url=wsdl)

    def setUp(self):
        super().setUp()  # type: ignore

        self.addCleanup(clear_caches)  # type: ignore

        main_config_patcher = patch(
            "openforms.appointments.utils.AppointmentsConfig.get_solo",
            return_value=AppointmentsConfig(
                plugin="jcc", **self.extra_appointments_config
            ),
        )
        main_config_patcher.start()
        self.addCleanup(main_config_patcher.stop)  # type: ignore

        jcc_config_patcher = patch(
            "openforms.appointments.contrib.jcc.client.JccConfig.get_solo",
            return_value=JccConfig(service=self.soap_service),
        )
        jcc_config_patcher.start()
        self.addCleanup(jcc_config_patcher.stop)  # type: ignore
