import factory
from zgw_consumers.models import Service


class UriPathFaker(factory.Faker):
    def __init__(self, **kwargs):
        super().__init__("uri_path", **kwargs)

    def generate(self, extra_kwargs=None):
        uri_path = super().generate(extra_kwargs)
        # faker generates them without trailing slash, but let's make sure this stays true
        # zgw_consumers.Service normalizes api_root to append missing trailing slashes
        assert not uri_path.endswith("/")
        return f"{uri_path}/"


class ServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"API-{n}")
    api_root = UriPathFaker()  # FIXME: this should be a fully qualified URL

    class Meta:
        model = Service
        django_get_or_create = ("api_root",)

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
