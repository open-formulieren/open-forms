import factory

from ..models import QmaticConfig


class QmaticConfigFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory("openforms.restapis.tests.factories.RestAPIFactory")

    class Meta:
        model = QmaticConfig
