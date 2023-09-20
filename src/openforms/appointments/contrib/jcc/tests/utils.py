from pathlib import Path
from unittest.mock import patch

from zeep.client import Client

from openforms.utils.tests.cache import clear_caches
from soap.tests.factories import SoapServiceFactory

from ....models import AppointmentsConfig
from ..models import JccConfig

MOCK_DIR = Path(__file__).parent.resolve() / "mock"

WSDL = str(MOCK_DIR / "GenericGuidanceSystem2.wsdl")


def mock_response(filename: str):
    full_path = MOCK_DIR / filename
    return full_path.read_text()


ZEEP_CLIENT = Client(WSDL)
"""
Client singleton to avoid loading the WSDL over and over again, which takes up about
60-70% of actual test runtime.

Instantiating the client causes the WSDL to be loaded, so this performance penalty hits
only once.
"""


class MockConfigMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # type: ignore

        cls.soap_service = SoapServiceFactory.create(url=WSDL)

    def setUp(self):
        super().setUp()  # type: ignore

        self.addCleanup(clear_caches)  # type: ignore

        main_config_patcher = patch(
            "openforms.appointments.utils.AppointmentsConfig.get_solo",
            return_value=AppointmentsConfig(plugin="jcc"),
        )
        main_config_patcher.start()
        self.addCleanup(main_config_patcher.stop)  # type: ignore

        jcc_config_patcher = patch(
            "openforms.appointments.contrib.jcc.client.JccConfig.get_solo",
            return_value=JccConfig(service=self.soap_service),
        )
        jcc_config_patcher.start()
        self.addCleanup(jcc_config_patcher.stop)  # type: ignore

        build_client_patcher = patch(
            "openforms.appointments.contrib.jcc.client.build_client",
            return_value=ZEEP_CLIENT,
        )
        build_client_patcher.start()
        self.addCleanup(build_client_patcher.stop)  # type: ignore


NSMAP = {
    "soap-env": "http://schemas.xmlsoap.org/soap/envelope/",
    "ns0": "http://www.genericCBS.org/GenericCBS/",
}


def get_xpath(doc, xpath: str):
    return doc.xpath(xpath, namespaces=NSMAP)
