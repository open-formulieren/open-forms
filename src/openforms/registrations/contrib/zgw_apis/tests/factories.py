import factory
from zgw_consumers.constants import APITypes

from ..models import ZGWApiGroupConfig


class ZGWApiGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "ZGW API set %03d" % n)
    zrc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.zrc
    )
    drc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.drc
    )
    ztc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.ztc
    )

    class Meta:
        model = ZGWApiGroupConfig
