from django.utils.translation import gettext_lazy as _

import requests
from zds_client.client import ClientError

from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.contrib.objects_api.models import ObjectsAPIConfig


def check_config():
    config = ObjectsAPIConfig.get_solo()

    services = (
        (
            "objects_service",
            "Objecten API",
            "object",
        ),
        (
            "drc_service",
            "Documenten API",
            "enkelvoudiginformatieobject",
        ),
    )
    for service_field, api_name, api_operation in services:
        service = getattr(config, service_field)
        if not service:
            raise InvalidPluginConfiguration(
                _("{api_name} endpoint is not configured.").format(api_name=api_name)
            )

        try:
            client = service.build_client()
            client.list(api_operation)
        except ClientError as e:
            e = e.__cause__ or e
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=e)
            )
        except Exception as e:
            raise InvalidPluginConfiguration(
                _("Could not connect to {api_name}: {exception}").format(
                    api_name=api_name, exception=e
                )
            )

    urls = [
        "objecttype",
        "informatieobjecttype_submission_report",
        "informatieobjecttype_submission_csv",
        "informatieobjecttype_attachment",
    ]
    for service_field in urls:
        url = getattr(config, service_field)
        if not url:
            # they are all optional defaults
            continue

        try:
            res = requests.get(url)
        except Exception as e:
            raise InvalidPluginConfiguration(
                _(
                    "Could not access default '{service_field}' ({url}): {exception}"
                ).format(service_field=service_field, url=url, exception=e)
            )
        else:
            if res.status_code not in (200, 403):
                raise InvalidPluginConfiguration(
                    _(
                        "Could not access default '{service_field}' ({url}): {exception}"
                    ).format(
                        service_field=service_field,
                        url=url,
                        exception=f"HTTP status {res.status_code}",
                    )
                )

    fields = [
        "productaanvraag_type",
        "objecttype_version",
        "organisatie_rsin",
    ]
    for service_field in fields:
        value = getattr(config, service_field)
        if not value:
            raise InvalidPluginConfiguration(
                _("Empty or invalid value for '{field}'").format(field=service_field)
            )
