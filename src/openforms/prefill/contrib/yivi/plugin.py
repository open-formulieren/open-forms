from collections.abc import Iterable
from typing import TypedDict

from django.utils.translation import gettext, gettext_lazy as _

import structlog
from glom import Coalesce, glom

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.constants import (
    PLUGIN_ID as AUTH_PLUGIN_ID,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.submissions.models import Submission
from openforms.typing import JSONEncodable, JSONObject

from ...base import BasePlugin
from ...exceptions import PrefillSkipped
from ...registry import register

logger = structlog.stdlib.get_logger(__name__)

MISSING = object()


class YiviOptions(TypedDict):
    pass


@register("yivi")
class YiviPrefill(BasePlugin[YiviOptions]):
    verbose_name = _("Yivi")
    requires_auth = (AuthAttribute.bsn, AuthAttribute.kvk, AuthAttribute.pseudo)
    requires_auth_plugin = (AUTH_PLUGIN_ID,)

    @staticmethod
    def get_available_attributes() -> Iterable[tuple[str, str]]:
        # Yivi attributes are dynamic because they depend on the selected attribute
        # groups in the authentication plugin options. A custom UI component handles
        # this.
        return ()

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, JSONEncodable]:
        if identifier_role != IdentifierRoles.main:
            raise PrefillSkipped("Skipping prefill for non-main identifier role.")

        glom_spec: dict[str, str | Coalesce] = {}

        for attribute in attributes:
            match attribute:
                # generic identifier attribute -> always read it from the auth info
                case "_internal.auth_info.value":
                    glom_spec[attribute] = "value"
                # only expose AuthAttribute.foo if that's what was actually provided
                # during auth
                case str(x) if x.startswith("_internal."):
                    requested_attr = x.removeprefix("_internal.")
                    if submission.auth_info.attribute == requested_attr:
                        glom_spec[attribute] = "value"
                # unknown fixed names -> look them up in the additional_claims JSON
                # struct
                case _:
                    glom_spec[attribute] = Coalesce(
                        f"additional_claims.{attribute}", default=MISSING
                    )

        values = glom(submission.auth_info, glom_spec)

        # remove the `None` defaults. we deliberately don't log these missing keys, as
        # the end-user decides if they expose the attribute(s) or not
        for key in list(values.keys()):
            if values[key] is not MISSING:
                continue
            del values[key]

        return values

    @classmethod
    def configuration_context(cls) -> JSONObject | None:
        return {
            # supported `AuthAttribute` to get a very specific one + one generic
            # "auth identifier" that returns just the value whatever the type may be.
            # The prefix marker is handled explicitly during prefilling.
            "fixed_attributes": [
                {
                    "attribute": "_internal.auth_info.value",
                    "label": gettext("Identifier value"),
                    "auth_attribute": "",
                },
                *(
                    {
                        "attribute": f"_internal.{auth_attr.value}",
                        "label": str(auth_attr.label),
                        "auth_attribute": auth_attr.value,
                    }
                    for auth_attr in cls.requires_auth
                ),
            ],
        }

    def check_config(self):
        pass
