import factory
from zgw_consumers.models import Service

from openforms.registrations.contrib.zgw_rest.models import ZgwConfig


class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Service


class ZgwConfigFactory(factory.django.DjangoModelFactory):
    zrc_service = factory.SubFactory(ServiceFactory)
    drc_service = factory.SubFactory(ServiceFactory)
    ztc_service = factory.SubFactory(ServiceFactory)

    class Meta:
        model = ZgwConfig
