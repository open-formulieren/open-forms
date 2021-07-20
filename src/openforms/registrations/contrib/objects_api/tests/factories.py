import factory
from zgw_consumers.constants import APITypes

from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory


class ObjectsAPIConfigFactory(factory.django.DjangoModelFactory):
    objects_service = factory.SubFactory(ServiceFactory, api_type=APITypes.orc)

    class Meta:
        model = ObjectsAPIConfig
