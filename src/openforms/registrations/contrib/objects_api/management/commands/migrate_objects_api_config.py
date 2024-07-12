from typing import Any

from django.core.management import BaseCommand

import requests

from openforms.forms.models import FormRegistrationBackend
from openforms.registrations.contrib.objects_api.models import ObjectsAPIGroupConfig

from ...client import get_catalogi_client
from ...plugin import PLUGIN_IDENTIFIER as OBJECTS_API_PLUGIN_IDENTIFIER

IOT_FIELDS = (
    "informatieobjecttype_submission_report",
    "informatieobjecttype_submission_csv",
    "informatieobjecttype_attachment",
)


class SkipBackend(Exception):
    """The backend options were already migrated."""


class InvalidBackend(Exception):
    """The backend options are invalid and can't be migrated."""

    def __init__(self, message: str, /) -> None:
        self.message = message


def migrate_registration_backend(options: dict[str, Any]) -> None:
    # idempotent check:
    if "catalogus_domein" in options:
        raise SkipBackend

    try:
        config = ObjectsAPIGroupConfig.objects.get(pk=options["objects_api_group"])
    except ObjectsAPIGroupConfig.DoesNotExist:
        raise InvalidBackend("The configured objects API group does not exist")

    iot_omschrijving: dict[str, str] = {}

    with get_catalogi_client(config) as catalogi_client:
        catalogus_domein: str | None = None
        catalogus_rsin: str | None = None

        for field in IOT_FIELDS:
            if url := options.get(field):
                try:
                    uuid = url.rsplit("/", 1)[1]
                except IndexError:
                    raise InvalidBackend(f"{field}: {url} is invalid")

                try:
                    iot = catalogi_client.get_informatieobjecttype(uuid)
                except requests.HTTPError as e:
                    if (status := e.response.status_code) == 404:
                        raise InvalidBackend(f"{field}: {url} does not exist")
                    else:
                        raise RuntimeError(
                            f"Encountered {status} error when fetching informatieobjecttype {uuid}"
                        )

                catalogus_resp = catalogi_client.get(iot["catalogus"])
                if not catalogus_resp.ok:
                    raise RuntimeError(
                        f"Encountered {catalogus_resp.status_code} error when fetching catalog {iot['catalogus']}"
                    )
                catalogus = catalogus_resp.json()

                if catalogus_domein is None and catalogus_rsin is None:
                    catalogus_domein = catalogus["domein"]
                    catalogus_rsin = catalogus["rsin"]
                else:
                    if (
                        catalogus["domein"] != catalogus_domein
                        or catalogus["rsin"] != catalogus_rsin
                    ):
                        raise InvalidBackend(
                            "Informatieobjecttypes don't share the same catalog"
                        )

                iot_omschrijving[field] = iot["omschrijving"]

    if catalogus_domein is not None and catalogus_rsin is not None:
        options["catalogus_domein"] = catalogus_domein
        options["catalogus_rsin"] = catalogus_rsin

        for field in IOT_FIELDS:
            if field in iot_omschrijving:
                options[field] = iot_omschrijving[field]


class Command(BaseCommand):
    help = (
        "Migrate existing Objects API form registration backends "
        "to switch from an informatieobjectype URL to a omschrijving and catalogus."
    )

    def handle(self, **options):
        for registration_backend in FormRegistrationBackend.objects.filter(
            backend=OBJECTS_API_PLUGIN_IDENTIFIER
        ):
            backend_name = registration_backend.name

            try:
                migrate_registration_backend(registration_backend.options)
            except SkipBackend:
                self.stdout.write(f"{backend_name!r} was already migrated")
            except InvalidBackend as e:
                self.stderr.write(
                    f"{backend_name!r} configuration is invalid: {e.message!r}"
                )
            except RuntimeError as e:
                self.stderr.write(
                    f"Encountered runtime error when trying to migrate {backend_name!r}: {e.args[0]!r}"
                )
            else:
                registration_backend.save()
