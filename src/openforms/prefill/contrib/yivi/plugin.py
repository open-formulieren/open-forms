from django.utils.translation import gettext_lazy as _

import structlog
from glom import Coalesce, glom

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.constants import (
    PLUGIN_ID as AUTH_PLUGIN_ID,
)
from openforms.prefill.base import BasePlugin
from openforms.prefill.constants import IdentifierRoles
from openforms.prefill.registry import register
from openforms.submissions.models import Submission
from openforms.typing import JSONEncodable

from .constants import PLUGIN_IDENTIFIER

logger = structlog.stdlib.get_logger(__name__)

MISSING = object()


@register(PLUGIN_IDENTIFIER)
class YiviPrefill(BasePlugin):
    verbose_name = _("Yivi")
    requires_auth = (
        AuthAttribute.bsn,
        AuthAttribute.kvk,
        AuthAttribute.pseudo,
    )
    requires_auth_plugin = (AUTH_PLUGIN_ID,)

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
    ) -> dict[str, JSONEncodable]:
        spec = {attr: Coalesce(attr, default=MISSING) for attr in attributes}
        values = glom(submission.auth_info, spec)

        # remove the `None` defaults
        for key in list(values.keys()):
            if values[key] is not MISSING:
                continue
            del values[key]
            logger.warning(
                "missing_attribute_in_auth_info",
                attribute=key,
            )

        return values

    def check_config(self):
        pass
