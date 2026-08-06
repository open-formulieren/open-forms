from django.utils.encoding import force_str
from django.utils.translation import gettext as _

from flags.state import flag_enabled
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.config.constants import UploadFileType
from openforms.config.models import (
    GlobalConfiguration,
    MapTileLayer,
    MapWMSTileLayer,
    RichTextColor,
)
from openforms.formio.registry import register as component_registry
from openforms.typing import JSONValue


def get_rich_text_colors():
    colors = list(RichTextColor.objects.values("color", "label"))
    if not colors:
        colors = [
            {"color": "red", "label": force_str(_("Red"))},
        ]
    return colors


def get_map_tile_layers():
    return list(MapTileLayer.objects.values("identifier", "url", "label"))


def get_wms_layers():
    return list(MapWMSTileLayer.objects.values("uuid", "name", "url"))


def get_component_empty_values():
    empty_values: dict[str, dict[str, JSONValue | None]] = {}
    for component_plugin in component_registry:
        empty_values[component_plugin.identifier] = {}

        for multiple in (True, False):
            _component_mock = {
                "type": component_plugin.identifier,
                "multiple": multiple,
                "key": "dummy",
                "label": "Dummy",
                # digitalAddressTypes is needed for customerProfile component
                "digitalAddressTypes": ["email", "phoneNumber"],
            }
            empty_value = component_registry.get_empty_value(_component_mock)
            json_safe_empty_value = (
                empty_value if empty_value is not NotImplemented else None
            )

            key = f"empty_value_{'multiple' if multiple else 'single'}"
            empty_values[component_plugin.identifier][key] = json_safe_empty_value

    return empty_values


class FormioConfigMixin:
    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        config = GlobalConfiguration.get_solo()
        context.update(
            {
                "required_default": config.form_fields_required_default,
                "rich_text_colors": get_rich_text_colors(),
                "map_tile_layers": get_map_tile_layers(),
                "wms_layers": get_wms_layers(),
                "upload_filetypes": [
                    {"label": label, "value": value}
                    for value, label in UploadFileType.choices
                ],
                "feature_flags": {
                    "ZGW_APIS_INCLUDE_DRAFTS": flag_enabled(
                        "ZGW_APIS_INCLUDE_DRAFTS", request=request
                    ),
                },
                "confidentiality_levels": [
                    {"label": label, "value": value}
                    for value, label in VertrouwelijkheidsAanduidingen.choices
                ],
                "component_empty_values": get_component_empty_values(),
            }
        )

        return super().render_change_form(request, context, add, change, form_url, obj)
