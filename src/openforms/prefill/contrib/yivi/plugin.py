from itertools import chain
from typing import Any

from django.utils.translation import gettext_lazy as _

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.constants import (
    PLUGIN_ID as YIVI_PLUGIN_ID,
)
from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.config.data import Action
from openforms.forms.models import FormAuthenticationBackend
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...registry import register
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
        # @TODO get real form id
        try:
            auth_backend = FormAuthenticationBackend.objects.get(
                backend=YIVI_PLUGIN_ID,
                form=58
            )
        except FormAuthenticationBackend.DoesNotExist:
            return []

        attributes_to_add = AttributeGroup.objects.filter(
            name__in=auth_backend.options.get("additional_attributes_groups", [])
        ).values_list("attributes", flat=True)

        attributes = []
        for attribute in list(chain.from_iterable(attributes_to_add)):
            attributes.append((attribute, _(attribute.split(".")[-1])))

        return attributes

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, Any]:
        if not submission.is_authenticated or not (
            cls.requires_auth and submission.auth_info.attribute in cls.requires_auth
        ):
            return {}

        prefill_values: dict[str, Any] = {}
        for attribute in attributes:
            prefill_values[attribute] = submission.auth_info.additional_claims.get(attribute, "default value")

        return prefill_values


    def check_config(self) -> list[Action]:
        """
        Demo config is always valid.
        """
        return []
