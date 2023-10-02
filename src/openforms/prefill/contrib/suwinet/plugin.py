import logging

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from glom import glom

from openforms.authentication.constants import AuthAttribute
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission
from openforms.typing import JSONSerializable
from suwinet.client import NoServiceConfigured, SuwinetClient, get_client
from suwinet.constants import SERVICES
from suwinet.models import SuwinetConfig

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...registry import register

logger = logging.getLogger(__name__)


def _get_client() -> SuwinetClient | None:
    try:
        return get_client()
    except NoServiceConfigured:
        logger.warning("No service defined for Suwinet.")
    return None


@register("suwinet")
class SuwinetPrefill(BasePlugin):
    requires_auth = AuthAttribute.bsn
    verbose_name = _("Suwinet")

    @staticmethod
    def get_available_attributes():
        if not (client := _get_client()):
            return []
        with client:
            return [
                (f"{service_name}.{operation}", f"{service_name} > {operation}")
                for service_name in client
                for operation in SERVICES[service_name].operations
            ]

    def get_prefill_values(
        self,
        submission: Submission,
        attributes: list[str],
        identifier_role: str = IdentifierRoles.main,
    ) -> dict[str, JSONSerializable]:
        if not (
            (client := _get_client())
            and (bsn := self.get_identifier_value(submission, identifier_role))
        ):
            return {}

        def get_value(attr) -> dict | None:
            try:
                return glom(client, attr)(bsn)
            except Exception:
                logger.exception("Suwinet raised exception")
                return None

        with client:
            return {attr: value for attr in attributes if (value := get_value(attr))}

    def get_co_sign_values(
        self, identifier: str, submission: Submission | None = None
    ) -> tuple[dict[str, dict], str]:
        """
        Given an identifier, fetch the co-sign specific values.

        The return value is a dict keyed by field name as specified in
        ``self.co_sign_fields``.

        :param identifier: the unique co-signer identifier used to look up the details
          in the pre-fill backend.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.
        """
        raise NotImplementedError(
            "You must implement the 'get_co_sign_values' method."
        )  # pragma: nocover

    def check_config(self):
        try:
            client = get_client()
            # TODO: Try all endpoints test bsn
        except NoServiceConfigured as e:
            raise InvalidPluginConfiguration(
                _("Configuration error: {exception}").format(exception=e)
            )
        if not len(client):
            raise InvalidPluginConfiguration(
                _("No services found. Check the binding addresses or provide a wsdl.")
            )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:suwinet_suwinetconfig_change",
                    args=(SuwinetConfig.singleton_instance_id,),
                ),
            )
        ]
