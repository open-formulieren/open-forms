from django.utils.translation import gettext_lazy as _

import requests

from openforms.plugins.exceptions import InvalidPluginConfiguration

from .client import (
    NoServiceConfigured,
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


def check_config():
    configs = ObjectsAPIGroupConfig.objects.all()
    services = (
        (check_objects_service, "objects_service"),
        (check_objecttypes_service, "objecttypes_service"),
        (check_documents_service, "drc_service"),
    )
    for config in configs:
        # First, check that the necessary services are configured correctly.
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

        urls = [
            "objecttype",
            "informatieobjecttype_submission_report",
            "informatieobjecttype_submission_csv",
            "informatieobjecttype_attachment",
        ]
        # we don't know for sure that these URLs share the same base, so instead we use a
        # raw requests session to get connection pooling without tying this to the configured
        # services.
        with requests.Session() as session:
            error_template = _(
                "Could not access default '{service_field}' ({url}) for Objects API group {objects_api_group}: {exception}"
            )
            for service_field in urls:
                # these fields are optional defaults, but if configured, they need to point to
                # something that looks right.
                if not (url := getattr(config, service_field)):
                    continue

                # this is a deliberate non-authenticated call, a 403 means we're hitting a
                # valid endpoint
                try:
                    response = session.get(url)
                except requests.RequestException as exc:
                    raise InvalidPluginConfiguration(
                        error_template.format(
                            service_field=service_field,
                            url=url,
                            objects_api_group=config.name,
                            exception=exc,
                        )
                    ) from exc

                # okay, looks like a valid endpoint
                if response.status_code in (200, 403) or response.ok:
                    continue

                raise InvalidPluginConfiguration(
                    error_template.format(
                        service_field=service_field,
                        url=url,
                        objects_api_group=config.name,
                        exception=f"HTTP status {response.status_code}",
                    )
                )
