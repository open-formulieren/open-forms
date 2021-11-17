from django.utils.translation import gettext_lazy as _

from requests.models import HTTPError
from zds_client.client import ClientError

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.contrib.zgw_apis.models import ZgwConfig


def check_config():
    config = ZgwConfig.get_solo()

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

    for service_field, api_name, api_operation in services:

        # Check settings
        service = getattr(config, service_field)
        if not service:
            raise InvalidPluginConfiguration(
                _("{api_name} endpoint is not configured.").format(api_name=api_name)
            )

        # Check connection and API-response
        try:
            client = service.build_client()
            client.list(api_operation)
        except (HTTPError, ClientError) as e:
            raise InvalidPluginConfiguration(
                _("Invalid response from {api_name}: {exception}").format(
                    api_name=api_name, exception=e
                )
            )
        except Exception as e:
            raise InvalidPluginConfiguration(
                _("Could not connect to {api_name}: {exception}").format(
                    api_name=api_name, exception=e
                )
            )
