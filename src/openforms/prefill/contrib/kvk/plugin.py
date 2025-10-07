from typing import Any

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from glom import GlomError, glom
from requests import RequestException

from openforms.authentication.service import AuthAttribute
from openforms.contrib.kvk.api_models.basisprofiel import BasisProfiel
from openforms.contrib.kvk.client import NoServiceConfigured, get_kvk_profile_client
from openforms.contrib.kvk.models import KVKConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...exceptions import PrefillSkipped
from ...registry import register
from .constants import Attributes

logger = structlog.stdlib.get_logger(__name__)


def _select_address(items, type_):
    if not items:
        return None
    for item in items:
        if item.get("type") == type_:
            return item
    return items[0]  # fall back to the first one


@register("kvk-kvknumber")
class KVK_KVKNumberPrefill(BasePlugin):
    verbose_name = _("KvK Company by KvK number")

    requires_auth = (AuthAttribute.kvk,)

    @staticmethod
    def get_available_attributes() -> list[tuple[str, str]]:
        return Attributes.choices

    @classmethod
    def get_identifier_value(
        cls, submission: Submission, identifier_role: str
    ) -> str | None:
        if not submission.is_authenticated:
            return

        if (
            identifier_role == IdentifierRoles.main
            and cls.requires_auth
            and submission.auth_info.attribute in cls.requires_auth
        ):
            return submission.auth_info.value

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: str = IdentifierRoles.main,
    ) -> dict[str, Any]:
        # check if submission was logged in with the identifier we're interested
        if not (kvk_value := cls.get_identifier_value(submission, identifier_role)):
            raise PrefillSkipped("No CoC-number available.")

        try:
            with get_kvk_profile_client() as client:
                result = client.get_profile(kvk_value)
        except (RequestException, NoServiceConfigured):
            return {}

        cls.modify_result(result)

        values = dict()
        for attr in attributes:
            try:
                values[attr] = glom(result, attr)
            except GlomError as exc:
                logger.warning(
                    "missing_attribute_in_response", attribute=attr, exc_info=exc
                )
        return values

    @staticmethod
    def modify_result(result: BasisProfiel):
        # first try getting the addresses from the embedded 'hoofdvestiging'. Note that
        # this may be absent or empty depending on the type of company (see #1299).
        # If there are no addresses found, we try to get them from 'eigenaar' instead.
        addresses = glom(result, "_embedded.hoofdvestiging.adressen", default=None)
        if addresses is None:
            addresses = glom(result, "_embedded.eigenaar.adressen", default=None)

        # not a required field, meaning the key may be absent. If that's the case,
        # do nothing (it's better than crashing!)
        if addresses is None:
            return
        # Move the desired item from the unordered list to a known place
        address = _select_address(addresses, "bezoekadres")
        if address:
            result["bezoekadres"] = address  # type: ignore

        address = _select_address(addresses, "correspondentieadres")
        if address:
            result["correspondentieadres"] = address  # type: ignore

    def check_config(self):
        check_kvk = "68750110"
        try:
            with get_kvk_profile_client() as client:
                result = client.get_profile(check_kvk)
        except NoServiceConfigured as e:
            raise InvalidPluginConfiguration(
                _("Configuration error: {exception}").format(exception=e)
            )
        except RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=exc)
            )
        else:
            if not isinstance(result, dict):
                raise InvalidPluginConfiguration(_("Response not a dictionary"))
            num = result.get("kvkNummer", None)
            if num != check_kvk:
                raise InvalidPluginConfiguration(
                    _("Did not find kvkNummer='{kvk}' in results").format(kvk=check_kvk)
                )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:kvk_kvkconfig_change",
                    args=(KVKConfig.singleton_instance_id,),
                ),
            ),
        ]
