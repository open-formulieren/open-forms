import factory

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ..models import ServiceFetchConfiguration


class ServiceFetchConfigurationFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(ServiceFactory)

    class Meta:
        model = ServiceFetchConfiguration
