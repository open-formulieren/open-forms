from pathlib import Path

from django.core.files import File

from simple_certmanager.constants import CertificateTypes
from simple_certmanager.models import Certificate

TEST_FILES = Path(__file__).parent.resolve() / "data"


def make_certificate(key_pem: Path, certificate_pem: Path, label="EHerkenning"):
    with key_pem.open("rb") as key_file, certificate_pem.open("rb") as cert_file:
        cert = Certificate(
            label=label,
            type=CertificateTypes.key_pair,
            private_key=File(key_file, key_pem.name),
            public_certificate=File(cert_file, certificate_pem.name),
        )
        cert.save()
    return cert
