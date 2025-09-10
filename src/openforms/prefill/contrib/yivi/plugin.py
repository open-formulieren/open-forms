from typing import TypedDict

from django.utils.translation import gettext, gettext_lazy as _

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.yivi_oidc.constants import (
    PLUGIN_ID as AUTH_PLUGIN_ID,
)
from openforms.typing import JSONObject

from ...base import BasePlugin
from ...registry import register


class YiviOptions(TypedDict):
    pass


@register("yivi")
class YiviPrefill(BasePlugin[YiviOptions]):
    verbose_name = _("Yivi")
    requires_auth = (AuthAttribute.bsn, AuthAttribute.kvk, AuthAttribute.pseudo)
    requires_auth_plugin = (AUTH_PLUGIN_ID,)
    # do not expose the plugin to the 'prefill' tab of components
    for_components = ()

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
                        "label": auth_attr.label,
                        "auth_attribute": auth_attr.value,
                    }
                    for auth_attr in cls.requires_auth
                ),
            ],
        }

    def check_config(self):
        pass
