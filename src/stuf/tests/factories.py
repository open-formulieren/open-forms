import factory

from soap.tests.factories import SoapServiceFactory
from stuf.models import StufService


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
