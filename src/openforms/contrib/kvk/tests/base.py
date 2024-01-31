import json
from pathlib import Path
from typing import Literal
from unittest.mock import patch

from simple_certmanager.constants import CertificateTypes
from simple_certmanager.test.factories import CertificateFactory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.kvk.models import KVKConfig

TEST_FILES = Path(__file__).parent.resolve() / "files"

G1_ROOT = TEST_FILES / "Staat_der_Nederlanden_Private_Root_CA_-_G1.crt"

TestFileNames = Literal[
    "basisprofiel_response.json",
    "basisprofiel_response_vve.json",
    "zoeken_response.json",
]


def load_json_mock(name: TestFileNames):
    with (TEST_FILES / name).open("r") as f:
        return json.load(f)


# See https://developers.kvk.nl/documentation/testing
SERVER_CERT = CertificateFactory.build(
    label="Staat der Nederlanden Private Root CA - G1",
    type=CertificateTypes.cert_only,
    public_certificate__filepath=str(G1_ROOT),
)

KVK_SERVICE = ServiceFactory.build(
    api_root="https://api.kvk.nl/test/api/",
    oas="https://api.kvk.nl/test/api/",  # ignored/unused
    api_type=APITypes.orc,
    auth_type=AuthTypes.api_key,
    header_key="apikey",
    header_value="l7xx1f2691f2520d487b902f4e0b57a0b197",
    server_certificate=SERVER_CERT,
)


class KVKTestMixin:

    api_root = KVK_SERVICE.api_root

    def setUp(self):
        super().setUp()

        patcher = patch(
            "openforms.contrib.kvk.client.KVKConfig.get_solo",
            return_value=KVKConfig(service=KVK_SERVICE),
        )
        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)

        # ensure that the certificate exists on disk, even with SimpleTestCase
        g1_cert = Path(SERVER_CERT.public_certificate.path)
        if not g1_cert.exists():
            g1_cert.write_bytes(G1_ROOT.read_bytes())
