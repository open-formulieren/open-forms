import factory
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from ..models import ZGWApiGroupConfig


class ZGWApiGroupConfigFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"ZGW API set {n:03d}")
    identifier = factory.Sequence(lambda n: f"zgw-api-group-{n}")
    zrc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.zrc
    )
    drc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.drc
    )
    ztc_service = factory.SubFactory(
        "zgw_consumers.test.factories.ServiceFactory", api_type=APITypes.ztc
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
                secret="test_secret_key",
            ),
            drc_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8003/documenten/api/v1/",
                api_type=APITypes.drc,
                auth_type=AuthTypes.zgw,
                client_id="test_client_id",
                secret="test_secret_key",
            ),
            ztc_service=factory.SubFactory(
                ServiceFactory,
                api_root="http://localhost:8003/catalogi/api/v1/",
                api_type=APITypes.ztc,
                auth_type=AuthTypes.zgw,
                client_id="test_client_id",
                secret="test_secret_key",
            ),
        )
