from django.utils.translation import gettext_lazy as _

import requests

from openforms.plugins.exceptions import InvalidPluginConfiguration

from .client import get_catalogi_client, get_documents_client, get_zaken_client
from .models import ZGWApiGroupConfig


def check_zaken_service(config: ZGWApiGroupConfig):
    with get_zaken_client(config) as client:
        client.get("zaken")


def check_catalogi_service(config: ZGWApiGroupConfig):
    with get_catalogi_client(config) as client:
        client.get("zaaktypen")


def check_documents_service(config: ZGWApiGroupConfig):
    with get_documents_client(config) as client:
        client.get("enkelvoudiginformatieobjecten")


def check_config():
    configs = ZGWApiGroupConfig.objects.all()
    # We need to check 3 API's for this configuration.
    services = (
        (check_zaken_service, "zrc_service"),
        (check_documents_service, "drc_service"),
        (check_catalogi_service, "ztc_service"),
    )

    for config in configs:
        for check_function, field_name in services:
            api_name = ZGWApiGroupConfig._meta.get_field(field_name).verbose_name  # type: ignore

            try:
                check_function(config)
            except requests.RequestException as exc:
                raise InvalidPluginConfiguration(
                    _(
                        "Invalid response from {api_name} in ZGW API set {zgw_api_set}: {exception}"
                    ).format(api_name=api_name, zgw_api_set=config.name, exception=exc)
                ) from exc
            except Exception as exc:
                raise InvalidPluginConfiguration(
                    _(
                        "Could not connect to {api_name} in ZGW API set {zgw_api_set}: {exception}"
                    ).format(api_name=api_name, zgw_api_set=config.name, exception=exc)
                ) from exc
