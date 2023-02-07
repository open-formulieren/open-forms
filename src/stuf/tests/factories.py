from pathlib import Path

import factory

from stuf.models import SoapService, StufService

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


class SoapServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"soap-service-{n}")
    url = "http://zaken/soap/"

    class Meta:
        model = SoapService

    class Params:
        with_server_cert = factory.Trait(
            server_certificate=factory.SubFactory(
                CertificateFactory, public_certificate__filename="server.cert"
            ),
        )
        with_client_cert = factory.Trait(
            client_certificate=factory.SubFactory(
                CertificateFactory, public_certificate__filename="client.cert"
            ),
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
