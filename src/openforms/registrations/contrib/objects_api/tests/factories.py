import factory
from zgw_consumers.constants import APITypes

from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from zgw_consumers_ext.factories import ServiceFactory


class ObjectsAPIConfigFactory(factory.django.DjangoModelFactory):
    objects_service = factory.SubFactory(ServiceFactory, api_type=APITypes.orc)
    drc_service = factory.SubFactory(ServiceFactory, api_type=APITypes.drc)

    class Meta:
        model = ObjectsAPIConfig
