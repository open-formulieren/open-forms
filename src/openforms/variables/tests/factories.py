import factory

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ..models import ServiceFetchConfiguration


class ServiceFetchConfigurationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceFetchConfiguration

    service = factory.SubFactory(ServiceFactory)
