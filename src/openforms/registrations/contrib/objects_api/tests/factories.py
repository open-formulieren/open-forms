import factory
from zgw_consumers.constants import APITypes

from ..models import ObjectsAPIGroupConfig


class ObjectsAPIGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Objects API group {n:03}")
    objects_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.orc
    )
    objecttypes_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.orc
    )
    drc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.drc
    )
    catalogi_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.ztc
    )

    class Meta:
        model = ObjectsAPIGroupConfig
