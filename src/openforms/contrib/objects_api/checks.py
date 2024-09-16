from django.utils.translation import gettext_lazy as _

import requests

from openforms.plugins.exceptions import InvalidPluginConfiguration

from .clients import (
    NoServiceConfigured,
    get_catalogi_client,
    get_documents_client,
    get_objects_client,
    get_objecttypes_client,
)
from .models import ObjectsAPIGroupConfig


def check_objects_service(config: ObjectsAPIGroupConfig):
    with get_objects_client(config) as client:
        resp = client.get("objects", params={"pageSize": 1})
        resp.raise_for_status()
        if not 200 <= resp.status_code < 300:
            raise InvalidPluginConfiguration(
                _(
                    "Missing Objects API credentials for Objects API group {objects_api_group}"
                ).format(objects_api_group=config.name)
            )


def check_objecttypes_service(config: ObjectsAPIGroupConfig):
    with get_objecttypes_client(config) as client:
        resp = client.get("objecttypes", params={"pageSize": 1})
        resp.raise_for_status()
        if not 200 <= resp.status_code < 300:
            raise InvalidPluginConfiguration(
                _(
                    "Missing Objecttypes API credentials for Objects API group {objects_api_group}"
                ).format(objects_api_group=config.name)
            )


def check_documents_service(config: ObjectsAPIGroupConfig):
    with get_documents_client(config) as client:
        resp = client.get("enkelvoudiginformatieobjecten")
        resp.raise_for_status()


def check_catalogi_service(config: ObjectsAPIGroupConfig):
    with get_catalogi_client(config) as client:
        resp = client.get("informatieobjecttypen")

    resp.raise_for_status()


def check_config():
    configs = ObjectsAPIGroupConfig.objects.all()
    services = (
        (check_objects_service, "objects_service"),
        (check_objecttypes_service, "objecttypes_service"),
        (check_documents_service, "drc_service"),
        (check_catalogi_service, "catalogi_service"),
    )
    for config in configs:
        for check_function, field_name in services:
            api_name = ObjectsAPIGroupConfig._meta.get_field(field_name).verbose_name  # type: ignore
            try:
                check_function(config)
            except NoServiceConfigured as exc:
                raise InvalidPluginConfiguration(
                    _(
                        "{api_name} endpoint is not configured for Objects API group {objects_api_group}."
                    ).format(api_name=api_name, objects_api_group=config.name)
                ) from exc
            except requests.RequestException as exc:
                raise InvalidPluginConfiguration(
                    _("Client error: {exception}").format(exception=exc)
                )
