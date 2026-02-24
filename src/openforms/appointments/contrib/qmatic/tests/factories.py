import factory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory as _ServiceFactory

from ..models import QmaticConfig


class ServiceFactory(_ServiceFactory):
    api_root = factory.Sequence(lambda n: f"http://www.example{n}.com/api/")
    api_type = APITypes.orc
    auth_type = AuthTypes.no_auth


class QmaticConfigFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(ServiceFactory)

    class Meta:
        model = QmaticConfig
