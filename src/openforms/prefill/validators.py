from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from openforms.authentication.registry import register as auth_register
from openforms.forms.validation.base import BaseValidator
from openforms.forms.validation.registry import register
from openforms.typing import JSONObject

from .co_sign import (
    AUTH_ATTRIBUTE_TO_CONFIG_FIELD,
    PrefillConfig,
    get_default_plugin_for_auth_attribute,
)
from .fields import PrefillPluginChoiceField


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

        assert isinstance(auth_plugin_id, str)
        auth_plugin = auth_register[auth_plugin_id]

        default_plugin = get_default_plugin_for_auth_attribute(
            auth_plugin.provides_auth
        )
        if not default_plugin:
            config_field_name = AUTH_ATTRIBUTE_TO_CONFIG_FIELD[
                auth_plugin.provides_auth
            ]
            field = PrefillConfig._meta.get_field(config_field_name)
            assert isinstance(field, PrefillPluginChoiceField)
            raise ValidationError(
                _(
                    "The co-sign component requires the '{field_label}' "
                    "({config_verbose_name}) to be configured."
                ).format(
                    field_label=field.verbose_name,
                    config_verbose_name=PrefillConfig._meta.verbose_name,
                ),
                code="invalid",
            )
