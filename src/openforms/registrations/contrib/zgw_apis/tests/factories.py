import factory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from ..models import ZGWApiGroupConfig


class ZGWApiGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"ZGW API set {n:03d}")
    identifier = factory.Sequence(lambda n: f"zgw-api-group-{n}")
    zrc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory",
        api_type=APITypes.zrc,
        auth_type=AuthTypes.zgw,
        client_id="dummy",
        secret="09bc216b-d057-423d-88cc-3242ad1945e7",
    )
    drc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory",
        api_type=APITypes.drc,
        auth_type=AuthTypes.zgw,
        client_id="dummy",
        secret="7ff59dbe-86f7-4f21-b58e-f62c7db2aa01",
    )
    ztc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory",
        api_type=APITypes.ztc,
        auth_type=AuthTypes.zgw,
        client_id="dummy",
        secret="b9f0fc4d-0602-43e3-8dfe-c6e53796c2ff",
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = ZGWApiGroupConfig

    class Params:
        # See the docker compose fixtures for base URLs authentication values:
        for_test_docker_compose = factory.Trait(
            zrc_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8003/zaken/api/v1/",
                api_type=APITypes.zrc,
                auth_type=AuthTypes.zgw,
                client_id="test_client_id",
                secret="c134912d-583a-447c-8c04-4e2597f26436",
            ),
            drc_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8003/documenten/api/v1/",
                api_type=APITypes.drc,
                auth_type=AuthTypes.zgw,
                client_id="test_client_id",
                secret="c134912d-583a-447c-8c04-4e2597f26436",
            ),
            ztc_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8003/catalogi/api/v1/",
                api_type=APITypes.ztc,
                auth_type=AuthTypes.zgw,
                client_id="test_client_id",
                secret="c134912d-583a-447c-8c04-4e2597f26436",
            ),
        )
