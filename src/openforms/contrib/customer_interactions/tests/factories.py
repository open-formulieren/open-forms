import factory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from ..models import CustomerInteractionsAPIGroupConfig


class CustomerInteractionsAPIGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Customer interactions API group {n:03}")
    identifier = factory.Sequence(lambda n: f"customer-interactions-api-group-{n}")
    customer_interactions_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.kc
    )

    class Meta:
        model = CustomerInteractionsAPIGroupConfig

    class Params:
        # See the docker compose fixtures for base URLs authentication values:
        for_test_docker_compose = factory.Trait(
            customer_interactions_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8005/klantinteracties/api/v1/",
                api_type=APITypes.kc,
                header_key="Authorization",
                header_value="Token 9b17346dbb9493f967e6653bbcdb03ac2f7009fa",
                auth_type=AuthTypes.api_key,
            )
        )
