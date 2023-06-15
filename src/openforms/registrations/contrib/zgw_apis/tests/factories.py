import factory
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from ..models import ZGWApiGroupConfig


class UriPathFaker(factory.Faker):
    def __init__(self, **kwargs):
        super().__init__("uri_path", **kwargs)

    def generate(self, extra_kwargs=None):
        uri_path = super().generate(extra_kwargs)
        if not uri_path.endswith("/"):
            return f"{uri_path}/"
        return uri_path


class ServiceFactory(factory.django.DjangoModelFactory):
    api_root = UriPathFaker()

    class Meta:
        model = Service
        django_get_or_create = ("api_root",)


class ZGWApiGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "ZGW API set %03d" % n)
    zrc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.zrc)
    drc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.drc)
    ztc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.ztc)

    class Meta:
        model = ZGWApiGroupConfig
