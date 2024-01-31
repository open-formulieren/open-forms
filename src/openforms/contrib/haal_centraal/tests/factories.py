import os
from pathlib import Path

import factory
from factory.django import DjangoModelFactory
from simple_certmanager.constants import CertificateTypes
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from ..constants import BRPVersions
from ..models import HaalCentraalConfig

HC_BRP_PERSONEN_API_KEY = os.getenv("HC_BRP_PERSONEN_API_KEY", "placeholder_key")
# Seems to be a semi-public, non-organization specific URL, so deemed safe to not obfuscate
HC_BRP_PERSONEN_BASE_URL = (
    "https://lab.api.mijniconnect.nl/iconnect/apihcbrp/actueel/v2/"
)

FILES_DIR = Path(__file__).parent / "files"


if client_key_path := os.environ.get("HC_BRP_PERSONEN_CLIENT_KEY"):
    MTLS_CLIENT_KEY_KWARGS = {
        "with_client_cert": True,
        "client_certificate__with_private_key": True,
        "client_certificate__public_certificate__from_path": str(FILES_DIR / "pub.crt"),
        "client_certificate__private_key__from_path": client_key_path,
        "with_server_cert": True,
        "server_certificate__type": CertificateTypes.cert_only,
        "server_certificate__public_certificate__from_path": str(
            FILES_DIR / "server-chain.pem"
        ),
    }
else:
    MTLS_CLIENT_KEY_KWARGS = {
        # "client_certificate__public_certificate__from_path": str(DATA_DIR / "pub.cert")
        # "client_certificate__private_key__from_path": os.environ.get("SUWINET_CLIENT_KEY")
    }


class HaalCentraalConfigFactory(DjangoModelFactory):

    brp_personen_service = factory.SubFactory(
        ServiceFactory,
        api_root=HC_BRP_PERSONEN_BASE_URL,
        auth_type=AuthTypes.api_key,
        header_key="x-api-key",
        header_value=HC_BRP_PERSONEN_API_KEY,
        **MTLS_CLIENT_KEY_KWARGS,
    )

    brp_personen_version = BRPVersions.v20

    class Meta:
        model = HaalCentraalConfig
