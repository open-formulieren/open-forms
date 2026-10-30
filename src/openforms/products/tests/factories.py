from decimal import Decimal

import factory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from ..models import Product


class ProductFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    price = Decimal("15.00")

    class Meta:
        model = Product


class OpenProductServiceFactory(ServiceFactory):
    class Params:
        # Service for testing against the docker container (test data taken from Open Product).
        # In order to use it, the container should be running, see details in the README file.
        for_test_docker_compose = factory.Trait(
            api_root="http://localhost:8006/",
            api_type=APITypes.ptc,
            header_key="Authorization",
            header_value="Token 75167ed1457337f6c27022ae772ba79a351b053a",
            auth_type=AuthTypes.api_key,
        )
