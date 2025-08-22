from django.utils.translation import gettext_lazy as _

import structlog
from glom import GlomError, glom

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.constants import (
    PLUGIN_ID as AUTH_PLUGIN_ID,
)
from openforms.prefill.base import BasePlugin
from openforms.prefill.constants import IdentifierRoles
from openforms.prefill.registry import register
from openforms.submissions.models import Submission

from .constants import PLUGIN_IDENTIFIER

logger = structlog.stdlib.get_logger(__name__)


@register(PLUGIN_IDENTIFIER)
class YiviPrefill(BasePlugin):
    verbose_name = _("Yivi")
    requires_auth_plugin = (AUTH_PLUGIN_ID,)
    requires_auth = (
        AuthAttribute.bsn,
        AuthAttribute.kvk,
        AuthAttribute.pseudo,
    )

    @staticmethod
    def get_available_attributes():
        """
        Return an empty list, and add the Yivi prefill attributes in the frontend.

        All Yivi prefill attributes are dependent on the configuration of the form:
        which authentication identifier would be available and which additional
        attributes are requested.

        The available prefill atttributes for the Yivi prefill plugin are all the Yivi
        attributes that are used during authentication. For this reason, we use the Yivi
        attributegroup API as the source of the Yivi prefill plugin attributes. To also
        include the atttributes used for fetching the authentication data (identifiers,
        loa values, etc.), we use `virtual` attributegroups. See the attributegroup API
        for additional information.
        """
        return []

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, object]:
        # Check if the user is authenticated using the required plugin, and resulted into
        # the right auth attribute.
        if (
            not submission.is_authenticated
            or not cls.verify_used_auth_plugin(submission)
            or not (
                cls.requires_auth
                and submission.auth_info.attribute in cls.requires_auth
            )
        ):
            return {}

        prefill_values: dict[str, object] = {}
        for attribute in attributes:
            try:
                prefill_values[attribute] = glom(submission.auth_info, attribute)
            except GlomError as exc:
                logger.warning(
                    "missing_attribute_in_response", attribute=attribute, exc_info=exc
                )

        return prefill_values

    def check_config(self):
        pass
