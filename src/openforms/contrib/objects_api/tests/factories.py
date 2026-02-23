import factory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from ..models import ObjectsAPIGroupConfig


class ObjectsAPIGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Objects API group {n:03}")
    identifier = factory.Sequence(lambda n: f"objects-api-group-{n}")
    objects_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory",
        api_type=APITypes.orc,
        auth_type=AuthTypes.no_auth,
    )
    objecttypes_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory",
        api_type=APITypes.orc,
        auth_type=AuthTypes.no_auth,
    )
    drc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory",
        api_type=APITypes.drc,
        auth_type=AuthTypes.zgw,
        client_id="dummy",
        secret="1a7b0352-f51b-4657-a96f-6d1ace6edf9e",
    )
    catalogi_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory",
        api_type=APITypes.ztc,
        auth_type=AuthTypes.zgw,
        client_id="dummy",
        secret="0eb98b79-6d0d-47ae-860c-848985a672d5",
    )

    class Meta:
        model = ObjectsAPIGroupConfig

    class Params:
        # See the docker compose fixtures for base URLs authentication values:
        for_test_docker_compose = factory.Trait(
            objects_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8002/api/v2/",
                api_type=APITypes.orc,
                header_key="Authorization",
                header_value="Token 7657474c3d75f56ae0abd0d1bf7994b09964dca9",
                auth_type=AuthTypes.api_key,
            ),
            objecttypes_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8001/api/v2/",
                api_type=APITypes.orc,
                header_key="Authorization",
                header_value="Token 171be5abaf41e7856b423ad513df1ef8f867ff48",
                auth_type=AuthTypes.api_key,
            ),
            drc_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8003/documenten/api/v1/",
                api_type=APITypes.drc,
                client_id="test_client_id",
                secret="c134912d-583a-447c-8c04-4e2597f26436",
                auth_type=AuthTypes.zgw,
            ),
            catalogi_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8003/catalogi/api/v1/",
                api_type=APITypes.ztc,
                client_id="test_client_id",
                secret="c134912d-583a-447c-8c04-4e2597f26436",
                auth_type=AuthTypes.zgw,
            ),
        )
