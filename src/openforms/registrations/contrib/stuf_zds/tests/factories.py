import factory

from openforms.registrations.contrib.stuf_zds.models import SoapService


class SoapServiceFactory(factory.django.DjangoModelFactory):
    ontvanger_organisatie = factory.Sequence(lambda n: f"ontvanger_organisatie-{n}")
    ontvanger_applicatie = factory.Sequence(lambda n: f"ontvanger_applicatie-{n}")
    # ontvanger_administratie = factory.Sequence(lambda n: f"ontvanger_administratie-{n}")
    # ontvanger_gebruiker = factory.Sequence(lambda n: f"ontvanger_gebruiker-{n}")

    zender_organisatie = factory.Sequence(lambda n: f"zender_organisatie-{n}")
    zender_applicatie = factory.Sequence(lambda n: f"zender_applicatie-{n}")
    # zender_administratie = factory.Sequence(lambda n: f"zender_administratie-{n}")
    # zender_gebruiker = factory.Sequence(lambda n: f"zender_gebruiker-{n}")

    url = "http://zaken/soap/"
    user = factory.Sequence(lambda n: f"user-{n}")
    password = factory.Sequence(lambda n: f"password-{n}")

    class Meta:
        model = SoapService
