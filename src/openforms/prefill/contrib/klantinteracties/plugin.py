from typing import TypedDict

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
import structlog

from openforms.authentication.service import AuthAttribute
from openforms.contrib.klantinteracties.client import get_klantinteracties_client
from openforms.contrib.klantinteracties.models import KlantinteractiesConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...exceptions import PrefillSkipped
from ...registry import register
from .constants import Attributes, DigitalAddressTypes

logger = structlog.stdlib.get_logger(__name__)

PLUGIN_IDENTIFIER = "klantinteracties"


class DigitalAddresses(TypedDict):
    phone_numbers: list[str]
    preferred_phone_number: str | None
    emails: list[str]
    preferred_email: str | None


class DigitalAddressResult(TypedDict):
    digital_addresses: DigitalAddresses


@register(PLUGIN_IDENTIFIER)
class klantinteractiesPlugin(BasePlugin):
    verbose_name = _("Klantinteracties API")
    requires_auth = (AuthAttribute.bsn,)

    @staticmethod
    def get_available_attributes() -> list[tuple[str, str]]:
        return Attributes.choices

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> DigitalAddressResult:
        # TODO changer implementation to get_prefill_values_from_options
        # TODO add kvk support

        result = DigitalAddresses(
            phone_numbers=[],
            preferred_phone_number=None,
            emails=[],
            preferred_email=None,
        )

        try:
            client = get_klantinteracties_client()
        except AssertionError:
            return DigitalAddressResult(digital_addresses=result)

        if not (bsn_value := cls.get_identifier_value(submission, identifier_role)):
            logger.info(
                "lookup_identifier_absent",
                submission_uuid=str(submission.uuid),
                plugin=cls,
            )
            raise PrefillSkipped("No BSN available.")

        digital_addresses = client.get_digital_addresses_for_bsn(bsn=bsn_value)

        for digital_address in digital_addresses:
            address = digital_address["adres"]
            match digital_address["soortDigitaalAdres"]:
                case DigitalAddressTypes.telefoonnummer:
                    result["phone_numbers"].append(address)
                    if digital_address["isStandaardAdres"]:
                        result["preferred_phone_number"] = address

                case DigitalAddressTypes.email:
                    result["emails"].append(address)
                    if digital_address["isStandaardAdres"]:
                        result["preferred_email"] = address

        return DigitalAddressResult(digital_addresses=result)

    def check_config(self):
        try:
            with get_klantinteracties_client() as client:
                resp = client.get("klantcontacten")
                resp.raise_for_status()

        except requests.RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Invalid response from Klantinteracties API: {exception}").format(
                    exception=exc
                )
            ) from exc
        except Exception as exc:
            raise InvalidPluginConfiguration(
                _("Could not connect to Klantinteracties API: {exception}").format(
                    exception=exc
                )
            ) from exc

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:klantinteracties_klantinteractiesconfig_change",
                    args=(KlantinteractiesConfig.singleton_instance_id,),
                ),
            ),
        ]
