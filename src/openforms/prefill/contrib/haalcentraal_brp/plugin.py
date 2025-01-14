import logging
from typing import Any

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
from glom import GlomError, glom

from openforms.authentication.service import AuthAttribute
from openforms.contrib.haal_centraal.clients import NoServiceConfigured, get_brp_client
from openforms.contrib.haal_centraal.clients.brp import BRPClient
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...registry import register
from .constants import AttributesV1, AttributesV2

logger = logging.getLogger(__name__)

PLUGIN_IDENTIFIER = "haalcentraal"

VERSION_TO_ATTRIBUTES_MAP = {
    BRPVersions.v13: AttributesV1,
    BRPVersions.v20: AttributesV2,
}


def get_attributes_cls():
    config = HaalCentraalConfig.get_solo()

    match config:
        case HaalCentraalConfig(
            brp_personen_version=version
        ) if version in VERSION_TO_ATTRIBUTES_MAP:
            return VERSION_TO_ATTRIBUTES_MAP[version]
        case _:
            return AttributesV1


@register(PLUGIN_IDENTIFIER)
class HaalCentraalPrefill(BasePlugin):
    verbose_name = _("Haal Centraal: BRP Personen Bevragen")
    requires_auth = (AuthAttribute.bsn,)

    @staticmethod
    def get_available_attributes() -> list[tuple[str, str]]:
        AttributesCls = get_attributes_cls()
        return AttributesCls.choices

    @classmethod
    def _get_values_for_bsn(
        cls,
        client: BRPClient,
        bsn: str,
        attributes: list[str],
    ) -> dict[str, Any]:
        if not (data := client.find_person(bsn, attributes=attributes)):
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

    @classmethod
    def get_identifier_value(
        cls, submission: Submission, identifier_role: IdentifierRoles
    ) -> str | None:
        if not submission.is_authenticated:
            return

        if (
            identifier_role == IdentifierRoles.main
            and cls.requires_auth
            and submission.auth_info.attribute in cls.requires_auth
        ):
            return submission.auth_info.value

        if identifier_role == IdentifierRoles.authorizee:
            auth_context = submission.auth_info.to_auth_context_data()
            # check if we have new-style authentication context capturing, and favour
            # that over the legacy format
            legal_subject = auth_context["authorizee"]["legalSubject"]
            # this only works if the identifier is a BSN
            if (
                "representee" not in auth_context
                or legal_subject["identifierType"] != "bsn"
            ):
                return None
            return legal_subject["identifier"]

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, Any]:
        try:
            client = get_brp_client(submission=submission)
        except NoServiceConfigured:
            return {}

        if not (bsn_value := cls.get_identifier_value(submission, identifier_role)):
            logger.info("No appropriate identifier found on the submission.")
            return {}

        with client:
            return cls._get_values_for_bsn(client, bsn_value, attributes)

    @classmethod
    def get_co_sign_values(
        cls, submission: Submission, identifier: str
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
        try:
            client = get_brp_client(submission=submission)
        except NoServiceConfigured:
            return ({}, "")

        Attributes = get_attributes_cls()
        with client:
            values = cls._get_values_for_bsn(
                client,
                identifier,
                (
                    Attributes.naam_voornamen,
                    Attributes.naam_voorvoegsel,
                    Attributes.naam_geslachtsnaam,
                    Attributes.naam_voorletters,
                ),
            )

        first_names = values.get(Attributes.naam_voornamen, "")
        first_letters = values.get(Attributes.naam_voorletters) or " ".join(
            [f"{name[0]}." for name in first_names.split(" ") if name]
        )
        representation_bits = [
            first_letters,
            values.get(Attributes.naam_voorvoegsel, ""),
            values.get(Attributes.naam_geslachtsnaam, ""),
        ]
        return (
            values,
            " ".join([bit for bit in representation_bits if bit]),
        )

    def check_config(self):
        """
        Check if the admin configuration is valid.

        The purpose of this fuction is to simply check the connection to the
        service, so we are using dummy data and an endpoint which does not exist.
        We want to avoid calls to the national registration by using a (valid) BSN.
        """
        try:
            with get_brp_client() as client:
                client.make_config_test_request()
        # Possibly no service or (valid) version is set.
        except NoServiceConfigured as exc:
            raise InvalidPluginConfiguration(_("Service not selected")) from exc
        except RuntimeError as exc:
            raise InvalidPluginConfiguration(exc.args[0]) from exc
        # The request itself can error
        except requests.RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=exc)
            ) from exc

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:haalcentraal_haalcentraalconfig_change",
                    args=(HaalCentraalConfig.singleton_instance_id,),
                ),
            ),
        ]
