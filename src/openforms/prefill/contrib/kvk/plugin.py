from collections.abc import Callable, Iterable
from typing import Any, assert_never

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from glom import GlomError, glom
from requests import RequestException

from openforms.authentication.service import AuthAttribute
from openforms.contrib.kvk.api_models.basisprofiel import (
    BasisProfiel,
    VestigingsProfiel,
)
from openforms.contrib.kvk.client import (
    KVKBranchProfileClient,
    KVKProfileClient,
    KVKProfileClientType,
    NoServiceConfigured,
    get_kvk_branch_profile_client,
    get_kvk_profile_client,
)
from openforms.contrib.kvk.models import KVKConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission
from openforms.typing import StrOrPromise

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
    def get_available_attributes() -> Iterable[tuple[str, StrOrPromise]]:
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
            if branch_number := submission.auth_info.legal_subject_service_restriction:
                return branch_number
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
            raise PrefillSkipped("No branch or CoC-number available.")

        client_function: Callable[[], KVKProfileClientType] = get_kvk_profile_client

        if submission.auth_info.legal_subject_service_restriction:
            client_function = get_kvk_branch_profile_client

        try:
            with client_function() as client:
                result = client.get_profile(kvk_value)
                cls.modify_result(result, client)
        except (RequestException, NoServiceConfigured):
            return {}

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
    def modify_result(
        result: BasisProfiel | VestigingsProfiel, client: KVKProfileClientType
    ):
        match client:
            case KVKProfileClient():
                addresses = glom(
                    result, "_embedded.hoofdvestiging.adressen", default=None
                )

                if addresses is None:
                    addresses = glom(
                        result, "_embedded.eigenaar.adressen", default=None
                    )
            case KVKBranchProfileClient():
                addresses = glom(result, "adressen", default=None)
            case _:  # pragma: no cover
                assert_never(client)

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
