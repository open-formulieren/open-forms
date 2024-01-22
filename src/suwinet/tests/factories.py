# See ./data/README!

import os
from pathlib import Path

import factory
from factory.django import DjangoModelFactory, FileField
from simple_certmanager.constants import CertificateTypes

from soap.constants import EndpointSecurity
from soap.tests.factories import SoapServiceFactory

from ..models import SuwinetConfig

DATA_DIR = Path(__file__).parent / "data"
FAKE_BASE_URL = "https://mygateway.example.com/SuwiML"
SUWINET_BASE_URL = os.environ.get("SUWINET_BASE_URL", FAKE_BASE_URL)


class SuwinetConfigFactory(DjangoModelFactory):
    class Meta:
        model = SuwinetConfig

    if "SUWINET_CLIENT_KEY" in os.environ:
        service = factory.SubFactory(
            SoapServiceFactory,
            url="",
            with_client_cert=True,
            client_certificate__type=CertificateTypes.key_pair,
            client_certificate__public_certificate=FileField(
                from_path=str(DATA_DIR / "pub.cert"),
            ),
            client_certificate__private_key=FileField(
                from_path=os.environ.get("SUWINET_CLIENT_KEY"),
            ),
            with_server_cert=True,
            server_certificate__type=CertificateTypes.cert_only,
            server_certificate__public_certificate=FileField(
                from_path=str(DATA_DIR / "server-chain.pem")
            ),
            endpoint_security=EndpointSecurity.wss,
        )
    else:
        service = factory.SubFactory(
            SoapServiceFactory,
            url="",
            with_client_cert=True,
            client_certificate__with_private_key=True,
            # client_certificate__type=CertificateTypes.key_pair,
            # client_certificate__public_certificate=FileField(
            #     from_path=str(DATA_DIR / "pub.cert")
            # ),
            # client_certificate__private_key=FileField(
            #     from_path=os.environ.get("SUWINET_CLIENT_KEY")
            # ),
            with_server_cert=True,
            server_certificate__type=CertificateTypes.cert_only,
            server_certificate__public_certificate=FileField(
                from_path=str(DATA_DIR / "server-chain.pem")
            ),
            endpoint_security=EndpointSecurity.wss,
        )

    class Params:
        all_endpoints = factory.Trait(
            bijstandsregelingen_binding_address=f"{SUWINET_BASE_URL}/Bijstandsregelingen-v0500/v1",
            brpdossierpersoongsd_binding_address=f"{SUWINET_BASE_URL}/BRPDossierPersoonGSD-v0200/v1",
            duodossierpersoongsd_binding_address=f"{SUWINET_BASE_URL}/DUODossierPersoonGSD-v0300/v1",
            duodossierstudiefinancieringgsd_binding_address=f"{SUWINET_BASE_URL}/DUODossierStudiefinancieringGSD-v0200/v1",
            gsddossierreintegratie_binding_address=f"{SUWINET_BASE_URL}/GSDDossierReintegratie-v0200/v1",
            ibverwijsindex_binding_address=f"{SUWINET_BASE_URL}/IBVerwijsindex-v0300/v1",
            kadasterdossiergsd_binding_address=f"{SUWINET_BASE_URL}/KadasterDossierGSD-v0300/v1",
            rdwdossierdigitalediensten_binding_address=f"{SUWINET_BASE_URL}/RDWDossierDigitaleDiensten-v0200/v1",
            rdwdossiergsd_binding_address=f"{SUWINET_BASE_URL}/RDWDossierGSD-v0200/v1",
            svbdossierpersoongsd_binding_address=f"{SUWINET_BASE_URL}/SVBDossierPersoonGSD-v0200/v1",
            uwvdossieraanvraaguitkeringstatusgsd_binding_address=f"{SUWINET_BASE_URL}/UWVDossierAanvraagUitkeringStatusGSD-v0200/v1",
            uwvdossierinkomstengsddigitalediensten_binding_address=f"{SUWINET_BASE_URL}/UWVDossierInkomstenGSD-v0201/v1",
            uwvdossierinkomstengsd_binding_address=f"{SUWINET_BASE_URL}/UWVDossierInkomstenGSDDigitaleDiensten-v0200/v1",
            uwvdossierquotumarbeidsbeperktengsd_binding_address=f"{SUWINET_BASE_URL}/UWVDossierQuotumArbeidsbeperktenGSD-v0300/v1",
            uwvdossierwerknemersverzekeringengsddigitalediensten_binding_address=f"{SUWINET_BASE_URL}/UWVDossierWerknemersverzekeringenGSD-v0200/v1",
            uwvdossierwerknemersverzekeringengsd_binding_address=f"{SUWINET_BASE_URL}/UWVDossierWerknemersverzekeringenGSDDigitaleDiensten-v0200/v1",
            uwvwbdossierpersoongsd_binding_address=f"{SUWINET_BASE_URL}/UWVWbDossierPersoonGSD-v0300/v1",
        )
