import factory
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from ..models import ZGWApiGroupConfig


class ServiceFactory(factory.django.DjangoModelFactory):
    api_root = factory.Faker("uri_path")

    class Meta:
        model = Service


class ZGWApiGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "ZGW API set %03d" % n)
    zrc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.zrc)
    drc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.drc)
    ztc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.ztc)

    class Meta:
        model = ZGWApiGroupConfig
