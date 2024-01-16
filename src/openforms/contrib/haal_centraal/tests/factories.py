import os
from pathlib import Path

import factory
from factory.django import DjangoModelFactory, FileField
from simple_certmanager.constants import CertificateTypes
from zgw_consumers.constants import AuthTypes

from zgw_consumers_ext.tests.factories import ServiceFactory

from ..constants import BRPVersions
from ..models import HaalCentraalConfig

HC_BRP_PERSONEN_API_KEY = os.getenv("HC_BRP_PERSONEN_API_KEY", "placeholder_key")
FAKE_BASE_URL = "https://example.com/"
HC_BRP_PERSONEN_BASE_URL = os.getenv("HC_BRP_PERSONEN_BASE_URL", FAKE_BASE_URL)

FILES_DIR = Path(__file__).parent / "files"


class HaalCentraalConfigFactory(DjangoModelFactory):

    if "HC_BRP_PERSONEN_CLIENT_KEY" in os.environ:
        brp_personen_service = factory.SubFactory(
            ServiceFactory,
            with_client_cert=True,
            with_server_cert=True,
            api_root=HC_BRP_PERSONEN_BASE_URL,
            auth_type=AuthTypes.api_key,
            header_key="x-api-key",
            header_value=HC_BRP_PERSONEN_API_KEY,
            client_certificate__type=CertificateTypes.key_pair,
            client_certificate__public_certificate=FileField(
                from_path=str(FILES_DIR / "pub.crt"),
            ),
            client_certificate__private_key=FileField(
                from_path=os.getenv("HC_BRP_PERSONEN_CLIENT_KEY"),
            ),
            server_certificate__type=CertificateTypes.cert_only,
            server_certificate__public_certificate=FileField(
                from_path=str(FILES_DIR / "server-chain.pem")
            ),
        )
    else:
        brp_personen_service = factory.SubFactory(
            ServiceFactory,
            api_root=HC_BRP_PERSONEN_BASE_URL,
            auth_type=AuthTypes.api_key,
            header_key="x-api-key",
            header_value=HC_BRP_PERSONEN_API_KEY,
        )

    brp_personen_version = BRPVersions.v20

    class Meta:
        model = HaalCentraalConfig
