import factory
from zgw_consumers.models import Service

from openforms.registrations.contrib.zgw_rest.models import ZgwConfig


class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Service


class ZgwConfigFactory(factory.django.DjangoModelFactory):
    zrc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.zrc)
    drc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.drc)
    ztc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.ztc)

    class Meta:
        model = ZgwConfig
