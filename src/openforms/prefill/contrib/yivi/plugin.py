from django.utils.translation import gettext_lazy as _

from openforms.authentication.constants import AuthAttribute
from openforms.config.data import Action
from openforms.prefill.base import BasePlugin
from openforms.prefill.constants import IdentifierRoles
from openforms.prefill.registry import register
from openforms.submissions.models import Submission

from .constants import PLUGIN_IDENTIFIER


@register(PLUGIN_IDENTIFIER)
class YiviPrefill(BasePlugin):
    verbose_name = _("Yivi")
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
        if not submission.is_authenticated or not (
            cls.requires_auth and submission.auth_info.attribute in cls.requires_auth
        ):
            return {}

        prefill_values: dict[str, object] = {}
        for attribute in attributes:
            # @TODO could also include auth info attributes
            prefill_values[attribute] = submission.auth_info.additional_claims.get(
                attribute, ""
            )

        return prefill_values

    def check_config(self) -> list[Action]:
        # @TODO
        return []
