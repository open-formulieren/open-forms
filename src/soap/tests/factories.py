import factory

from ..models import SoapService


class SoapServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"soap-service-{n}")
    url = "http://zaken/soap/"

    class Meta:
        model = SoapService

    class Params:
        with_server_cert = factory.Trait(
            server_certificate=factory.SubFactory(
                "simple_certmanager.test.factories.CertificateFactory",
                public_certificate__filename="server.cert",
            ),
        )
        with_client_cert = factory.Trait(
            client_certificate=factory.SubFactory(
                "simple_certmanager.test.factories.CertificateFactory",
                public_certificate__filename="client.cert",
            ),
        )
