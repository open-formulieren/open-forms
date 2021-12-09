from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from openforms.authentication.registry import register as auth_register
from openforms.forms.validation.base import BaseValidator
from openforms.forms.validation.registry import register
from openforms.typing import JSONObject

from .co_sign import get_default_plugin_for_auth_attribute


@register("coSign")
class CoSignValidator(BaseValidator):
    def __call__(self, component: JSONObject) -> None:
        if not (auth_plugin_id := component.get("authPlugin")):
            raise ValidationError(
                _(
                    "The co-sign component is missing the authPlugin configuration option"
                ),
                code="invalid",
            )

        auth_plugin = auth_register[auth_plugin_id]
        default_plugin = get_default_plugin_for_auth_attribute(
            auth_plugin.provides_auth
        )
        if not default_plugin:
            raise ValidationError(
                _(
                    "The co-sign component would look up the name by '{attr}', but the "
                    "global prefill default is not (yet) configured for this."
                ).format(attr=auth_plugin.provides_auth),
                code="invalid",
            )
