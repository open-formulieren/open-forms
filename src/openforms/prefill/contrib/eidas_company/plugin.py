from django.utils.translation import gettext_lazy as _

import structlog
from glom import GlomError, glom
from mozilla_django_oidc_db.models import OIDCClient

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.digid_eherkenning_oidc.constants import (
    EIDAS_COMPANY_PLUGIN_ID,
)
from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.constants import (
    OIDC_EIDAS_COMPANY_IDENTIFIER,
)
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.base import BasePlugin
from openforms.prefill.constants import IdentifierRoles
from openforms.prefill.registry import register
from openforms.submissions.models import Submission

from .constants import REQUIRED_CLIENT_IDENTITY_SETTINGS, Attributes

PLUGIN_IDENTIFIER = "eidas_company"

logger = structlog.stdlib.get_logger(__name__)


@register(PLUGIN_IDENTIFIER)
class EIDASCompanyPrefill(BasePlugin):
    verbose_name = _("eIDAS company")
    requires_auth = (
        AuthAttribute.bsn,
        AuthAttribute.pseudo,
    )
    requires_auth_plugin = (EIDAS_COMPANY_PLUGIN_ID,)

    @staticmethod
    def get_available_attributes():
        return Attributes.choices

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, str]:
        """
        Given the requested attributes, look up the appropriate values and return them.

        :param submission: an active :class:`Submission` instance, which can be supply
          the required context to fetch the correct prefill values.
        :param attributes: a list of requested prefill attributes, provided in bulk
          to efficiently fetch as much data as possible with the minimal amount of calls.
        """
        # Check if authentication was done with the required plugin, and resulted into
        # the right auth attribute.
        if not cls.verify_used_auth_plugin(submission):
            return {}

        # To easily fetch the identifier and identifier-type data, we use the auth
        # context as data source.
        auth_context = submission.auth_info.to_auth_context_data()

        values = dict()
        for attr in attributes:
            try:
                values[attr] = glom(auth_context["authorizee"], attr)
            except GlomError as exc:
                logger.warning(
                    "missing_attribute_in_auth_context_authorizee",
                    attribute=attr,
                    exc_info=exc,
                )

        return values

    def check_config(self):
        try:
            client = OIDCClient.objects.get(
                identifier=OIDC_EIDAS_COMPANY_IDENTIFIER, enabled=True
            )
        except OIDCClient.DoesNotExist:
            raise InvalidPluginConfiguration(
                _("Missing OIDC client for eIDAS Company.")
            )

        if not client.options["identity_settings"]:
            raise InvalidPluginConfiguration(
                _("Missing OIDC client identity settings for eIDAS Company.")
            )

        # All the claims that are available for prefill should be configured.
        for setting in REQUIRED_CLIENT_IDENTITY_SETTINGS:
            if not len(client.options["identity_settings"].get(setting, [])):
                raise InvalidPluginConfiguration(
                    _("Missing OIDC client identity settings for eIDAS Company.")
                )
