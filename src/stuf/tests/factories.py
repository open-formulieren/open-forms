from pathlib import Path

import factory

from soap.tests.factories import SoapServiceFactory
from stuf.models import StufService

DATA_DIR = Path(__file__).parent.resolve() / "data"


class CertificateFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"certificate-{n}")
    type = "cert_only"
    public_certificate = factory.django.FileField(
        from_path=str(DATA_DIR / "test.certificate")
    )

    class Meta:
        model = "simple_certmanager.Certificate"

    class Params:
        with_private_key = factory.Trait(
            private_key=factory.django.FileField(from_path=str(DATA_DIR / "test.key"))
        )


class StufServiceFactory(factory.django.DjangoModelFactory):
    ontvanger_organisatie = factory.Sequence(lambda n: f"ontvanger_organisatie-{n}")
    ontvanger_applicatie = factory.Sequence(lambda n: f"ontvanger_applicatie-{n}")
    ontvanger_administratie = factory.Sequence(lambda n: f"ontvanger_administratie-{n}")
    ontvanger_gebruiker = factory.Sequence(lambda n: f"ontvanger_gebruiker-{n}")

    zender_organisatie = factory.Sequence(lambda n: f"zender_organisatie-{n}")
    zender_applicatie = factory.Sequence(lambda n: f"zender_applicatie-{n}")
    zender_administratie = factory.Sequence(lambda n: f"zender_administratie-{n}")
    zender_gebruiker = factory.Sequence(lambda n: f"zender_gebruiker-{n}")

    soap_service = factory.SubFactory(SoapServiceFactory)

    class Meta:
        model = StufService
