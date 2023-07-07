import logging
from typing import Any, Iterable, Optional

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from glom import GlomError, glom
from zds_client import ClientError

from openforms.authentication.constants import AuthAttribute
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.pre_requests.clients import PreRequestClientContext
from openforms.prefill.contrib.haalcentraal.constants import Attributes
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...registry import register
from .models import HaalCentraalConfig

logger = logging.getLogger(__name__)


def get_config() -> HaalCentraalConfig | None:
    config = HaalCentraalConfig.get_solo()
    assert isinstance(config, HaalCentraalConfig)
    if not config.service:
        logger.warning("No service defined for Haal Centraal prefill.")
        return None
    return config


@register("haalcentraal")
class HaalCentraalPrefill(BasePlugin):
    verbose_name = _("Haal Centraal")
    requires_auth = AuthAttribute.bsn

    @staticmethod
    def get_available_attributes() -> list[tuple[str, str]]:
        config = get_config()
        if config is None:
            return Attributes.choices
        return config.get_attributes().choices

    @classmethod
    def _get_values_for_bsn(
        cls,
        config: HaalCentraalConfig,
        submission: Submission | None,
        bsn: str,
        attributes: Iterable[str],
    ) -> dict[str, Any]:
        client = config.build_client()
        assert client is not None
        # FIXME: typing info on protocol
        client.context = PreRequestClientContext(submission=submission)

        data = client.find_person(bsn, attributes=attributes)
        if not data:
            return {}

        values = dict()
        for attr in attributes:
            try:
                values[attr] = glom(data, attr)
            except GlomError as exc:
                logger.warning(
                    "missing expected attribute '%s' in backend response",
                    attr,
                    exc_info=exc,
                )

        return values

    def get_identifier_value(
        self, submission: Submission, identifier_role: str
    ) -> str | None:
        if not submission.is_authenticated:
            return

        if (
            identifier_role == IdentifierRoles.main
            and submission.auth_info.attribute == self.requires_auth
        ):
            return submission.auth_info.value

        if identifier_role == IdentifierRoles.authorised_person:
            return submission.auth_info.machtigen.get("value")

    def get_prefill_values(
        self,
        submission: Submission,
        attributes: list[str],
        identifier_role: str = "main",
    ) -> dict[str, Any]:
        if (config := get_config()) is None:
            return {}

        if not (bsn_value := self.get_identifier_value(submission, identifier_role)):
            logger.info("No appropriate identifier found on the submission.")
            return {}

        return self._get_values_for_bsn(config, submission, bsn_value, attributes)

    @classmethod
    def get_co_sign_values(
        cls, identifier: str, submission: Optional["Submission"] = None
    ) -> tuple[dict[str, Any], str]:
        """
        Given an identifier, fetch the co-sign specific values.

        The return value is a dict keyed by field name as specified in
        ``self.co_sign_fields``.

        :param identifier: the unique co-signer identifier used to look up the details
          in the prefill backend.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.
        """
        config = get_config()
        if config is None:
            return ({}, "")

        version_atributes = config.get_attributes()

        values = cls._get_values_for_bsn(
            config,
            submission,
            identifier,
            (
                version_atributes.naam_voornamen,
                version_atributes.naam_voorvoegsel,
                version_atributes.naam_geslachtsnaam,
                version_atributes.naam_voorletters,
            ),
        )

        first_names = values.get(version_atributes.naam_voornamen, "")
        first_letters = values.get(version_atributes.naam_voorletters) or " ".join(
            [f"{name[0]}." for name in first_names.split(" ") if name]
        )
        representation_bits = [
            first_letters,
            values.get(version_atributes.naam_voorvoegsel, ""),
            values.get(version_atributes.naam_geslachtsnaam, ""),
        ]
        return (
            values,
            " ".join([bit for bit in representation_bits if bit]),
        )

    def check_config(self):
        try:
            config = HaalCentraalConfig.get_solo()
            assert isinstance(config, HaalCentraalConfig)
            if not config.service:
                raise InvalidPluginConfiguration(_("Service not selected"))

            client = config.service.build_client()
            # FIXME: haal centraal v2 client does not support GET methods
            client.retrieve("test", "test")
        except ClientError as e:
            if e.args[0].get("status") == 404:
                return
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=e)
            )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:prefill_haalcentraal_haalcentraalconfig_change",
                    args=(HaalCentraalConfig.singleton_instance_id,),
                ),
            ),
        ]
