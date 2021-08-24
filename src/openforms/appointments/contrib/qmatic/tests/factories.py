import factory
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from ..models import QmaticConfig


class ServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"API-{n}")
    api_root = factory.Sequence(lambda n: f"http://www.example{n}.com/api/v1/")
    api_type = APITypes.orc

    class Meta:
        model = Service


class QmaticConfigFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(ServiceFactory)

    class Meta:
        model = QmaticConfig
