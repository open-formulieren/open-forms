import factory
from zgw_consumers.models import Service

from openforms.forms.tests.factories import FormFactory

from ..models import ZgwConfig, ZGWFormConfig


class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Service


class ZgwConfigFactory(factory.django.DjangoModelFactory):
    zrc_service = factory.SubFactory(ServiceFactory)
    drc_service = factory.SubFactory(ServiceFactory)

    class Meta:
        model = ZgwConfig


class ZGWFormConfigFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = ZGWFormConfig
