from django.utils.translation import gettext_lazy as _

from requests.models import HTTPError
from zds_client.client import ClientError

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig


def check_config():
    configs = ZGWApiGroupConfig.objects.all()

    # We need to check 3 API's for this configuration.
    services = (
        (
            "zrc_service",
            "Zaken API",
            "zaak",
        ),
        (
            "drc_service",
            "Documenten API",
            "enkelvoudiginformatieobject",
        ),
        (
            "ztc_service",
            "Catalogi API",
            "zaaktype",
        ),
    )

    for config in configs:
        for service_field, api_name, api_resource in services:

            # Check settings
            service = getattr(config, service_field)
            if not service:
                raise InvalidPluginConfiguration(
                    _(
                        "{api_name} endpoint is not configured for ZGW API set {zgw_api_set}."
                    ).format(api_name=api_name, zgw_api_set=config.name)
                )

            # Check connection and API-response
            try:
                client = service.build_client()
                client.list(api_resource)
            except (HTTPError, ClientError) as e:
                raise InvalidPluginConfiguration(
                    _(
                        "Invalid response from {api_name} in ZGW API set {zgw_api_set}: {exception}"
                    ).format(api_name=api_name, zgw_api_set=config.name, exception=e)
                )
            except Exception as e:
                raise InvalidPluginConfiguration(
                    _(
                        "Could not connect to {api_name} in ZGW API set {zgw_api_set}: {exception}"
                    ).format(api_name=api_name, zgw_api_set=config.name, exception=e)
                )
