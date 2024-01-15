from django.utils.translation import gettext_lazy as _

import requests

from openforms.plugins.exceptions import InvalidPluginConfiguration

from .client import NoServiceConfigured, get_documents_client, get_objects_client
from .models import ObjectsAPIConfig


def check_objects_service():
    with get_objects_client() as client:
        client.get("objects")


def check_documents_service():
    with get_documents_client() as client:
        client.get("enkelvoudiginformatieobjecten")


def check_config():
    # First, check that the necessary services are configured correctly.
    services = (
        (check_objects_service, "objects_service"),
        (check_documents_service, "drc_service"),
    )

    for check_function, field_name in services:
        api_name = ObjectsAPIConfig._meta.get_field(field_name).verbose_name  # type: ignore
        try:
            check_function()
        except NoServiceConfigured as exc:
            raise InvalidPluginConfiguration(
                _("{api_name} endpoint is not configured.").format(api_name=api_name)
            ) from exc
        except requests.RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=exc)
            )

    config = ObjectsAPIConfig.get_solo()

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
            "Could not access default '{service_field}' ({url}): {exception}"
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
                        service_field=service_field, url=url, exception=exc
                    )
                ) from exc

            # okay, looks like a valid endpoint
            if response.status_code in (200, 403) or response.ok:
                continue

            raise InvalidPluginConfiguration(
                error_template.format(
                    service_field=service_field,
                    url=url,
                    exception=f"HTTP status {response.status_code}",
                )
            )
