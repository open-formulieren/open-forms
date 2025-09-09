from django.utils.translation import gettext_lazy as _

import structlog
from glom import Coalesce, glom
from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.typing import ClaimPath

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.digid_eherkenning_oidc.constants import (
    EIDAS_COMPANY_PLUGIN_ID,
    EIDAS_PLUGIN_ID,
)
from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.constants import (
    OIDC_EIDAS_COMPANY_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
)
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.base import BasePlugin
from openforms.prefill.constants import IdentifierRoles
from openforms.prefill.registry import register
from openforms.submissions.models import Submission
from openforms.typing import JSONEncodable

from .constants import (
    REQUIRED_CITIZEN_CLIENT_IDENTITY_SETTINGS,
    REQUIRED_COMPANY_CLIENT_IDENTITY_SETTINGS,
    CitizenAttributes,
    CompanyAttributes,
)

logger = structlog.stdlib.get_logger(__name__)

MISSING = object()


@register("eidas-citizen")
class EIDASCitizenPrefill(BasePlugin):
    verbose_name = _("eIDAS (citizen)")
    requires_auth = (
        AuthAttribute.bsn,
        AuthAttribute.pseudo,
    )
    requires_auth_plugin = (EIDAS_PLUGIN_ID,)

    @staticmethod
    def get_available_attributes():
        return CitizenAttributes.choices

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, JSONEncodable]:
        """
        Given the requested attributes, look up the appropriate values and return them.

        :param submission: an active :class:`Submission` instance, which can be supply
          the required context to fetch the correct prefill values.
        :param attributes: a list of requested prefill attributes, provided in bulk
          to efficiently fetch as much data as possible with the minimal amount of calls.
        """

        # To easily fetch the identifier and identifier-type data, we use the auth
        # context as data source.
        auth_context = submission.auth_info.to_auth_context_data()
        spec = {attr: Coalesce(attr, default=MISSING) for attr in attributes}
        values = glom(auth_context["authorizee"], spec)

        # remove the `None` defaults
        for key in list(values.keys()):
            if values[key] is not MISSING:
                continue
            del values[key]
            logger.warning(
                "missing_attribute_in_auth_context_authorizee",
                attribute=key,
            )

        return values

    def check_config(self):
        # check if we have an enabled client. Note that the mozilla-django-oidc-db
        # post_migrate hook ensures the defined clients exist in the DB.
        client = OIDCClient.objects.filter(
            identifier=OIDC_EIDAS_IDENTIFIER, enabled=True
        ).first()
        if client is None:
            raise InvalidPluginConfiguration(
                _("No enabled OIDC client for eIDAS (citizen) found.")
            )

        if not client.options["identity_settings"]:
            raise InvalidPluginConfiguration(
                _("Missing OIDC client identity settings for eIDAS.")
            )

        # All the claims that are available for prefill should be configured.
        missing_claim_paths: list[str] = []
        for setting in REQUIRED_CITIZEN_CLIENT_IDENTITY_SETTINGS:
            claim_path: ClaimPath = client.options["identity_settings"].get(setting, [])
            if not claim_path:
                missing_claim_paths.append(setting)

        if missing_claim_paths:
            raise InvalidPluginConfiguration(
                _(
                    "The eIDAS client identity settings are missing values for the "
                    "settings: {settings}."
                ).format(settings=", ".join(missing_claim_paths))
            )


@register("eidas-company")
class EIDASCompanyPrefill(BasePlugin):
    verbose_name = _("eIDAS (company)")
    requires_auth = (
        AuthAttribute.bsn,
        AuthAttribute.pseudo,
    )
    requires_auth_plugin = (EIDAS_COMPANY_PLUGIN_ID,)

    @staticmethod
    def get_available_attributes():
        return CompanyAttributes.choices

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, JSONEncodable]:
        """
        Given the requested attributes, look up the appropriate values and return them.

        :param submission: an active :class:`Submission` instance, which can be supply
          the required context to fetch the correct prefill values.
        :param attributes: a list of requested prefill attributes, provided in bulk
          to efficiently fetch as much data as possible with the minimal amount of calls.
        """
        # To easily fetch the identifier and identifier-type data, we use the auth
        # context as data source.
        auth_context = submission.auth_info.to_auth_context_data()
        spec = {attr: Coalesce(attr, default=MISSING) for attr in attributes}
        values = glom(auth_context["authorizee"], spec)

        # remove the `None` defaults
        for key in list(values.keys()):
            if values[key] is not MISSING:
                continue
            del values[key]
            logger.warning(
                "missing_attribute_in_auth_context_authorizee",
                attribute=key,
            )

        return values

    def check_config(self):
        # check if we have an enabled client. Note that the mozilla-django-oidc-db
        # post_migrate hook ensures the defined clients exist in the DB.
        client = OIDCClient.objects.filter(
            identifier=OIDC_EIDAS_COMPANY_IDENTIFIER, enabled=True
        ).first()
        if client is None:
            raise InvalidPluginConfiguration(
                _("No enabled OIDC client for eIDAS (company) found.")
            )

        if not client.options["identity_settings"]:
            raise InvalidPluginConfiguration(
                _("Missing OIDC client identity settings for eIDAS Company.")
            )

        # All the claims that are available for prefill should be configured.
        missing_claim_paths: list[str] = []
        for setting in REQUIRED_COMPANY_CLIENT_IDENTITY_SETTINGS:
            claim_path: ClaimPath = client.options["identity_settings"].get(setting, [])
            if not claim_path:
                missing_claim_paths.append(setting)

        if missing_claim_paths:
            raise InvalidPluginConfiguration(
                _(
                    "The eIDAS client identity settings are missing values for the "
                    "settings: {settings}."
                ).format(settings=", ".join(missing_claim_paths))
            )
