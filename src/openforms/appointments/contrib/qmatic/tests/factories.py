import factory
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from ..models import QmaticConfig


# TODO: consolidate this in src/openforms/contrib or src/zgw_consumers_ext
class ServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"API-{n}")
    api_root = factory.Sequence(lambda n: f"http://www.example{n}.com/api/")
    api_type = APITypes.orc

    class Meta:
        model = Service


class QmaticConfigFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(ServiceFactory)

    class Meta:
        model = QmaticConfig
