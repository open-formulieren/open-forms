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


type EmptyValueOption = tuple[str, bool, JSONValue]
"""
Data meaning: (component_type, multiple or not, associated empty value).
"""


def get_component_empty_values():
    # hack to pass the empty values, as it's not readily available in the
    # formio-renderer or formio-builder...
    # FIXME: build a proper solution for this.
    empty_values: list[EmptyValueOption] = []
    for component_plugin in component_registry:
        component_type = component_plugin.identifier
        # this completely ignores if multiple is supported for this component type or not...
        for multiple in (True, False):
            _component_mock = {
                "type": component_plugin.identifier,
                "multiple": multiple,
                "key": "dummy",
                "label": "Dummy",
            }
            # digitalAddressTypes is needed for customerProfile component
            if component_type == "customerProfile":
                _component_mock["digitalAddressTypes"] = ["email", "phoneNumber"]

            empty_value = component_registry.get_empty_value(_component_mock)  # pyright: ignore[reportArgumentType]
            if (
                empty_value is NotImplemented
            ):  # layout components don't have an empty value
                continue
            empty_values.append((component_type, multiple, empty_value))
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
