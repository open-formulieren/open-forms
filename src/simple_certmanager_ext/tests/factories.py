from pathlib import Path

import factory
from simple_certmanager.constants import CertificateTypes
from simple_certmanager.models import Certificate

DATA_DIR = Path(__file__).parent.resolve() / "data"


class CertificateFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"certificate-{n}")
    type = CertificateTypes.cert_only
    public_certificate = factory.django.FileField(
        from_path=str(DATA_DIR / "test.certificate"),
        filename="cert.pem",
    )

    class Meta:
        model = Certificate

    class Params:
        with_private_key = factory.Trait(
            type=CertificateTypes.key_pair,
            private_key=factory.django.FileField(
                from_path=str(DATA_DIR / "test.key"),
                filename="key.pem",
            ),
        )
