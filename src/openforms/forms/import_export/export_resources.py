from collections.abc import Mapping

from openforms.typing import JSONObject

from ..models import Form
from .datastructures import FormExportOptions
from .resources import (
    BaseResource,
    ProductResource,
    WMSTileLayerResource,
    WMTSTileLayerResource,
    YiviAttributeGroupResource,
)
from .typing import AdditionalFormConfigurationOptions

type ExportResourceConfig = tuple[type[BaseResource], str]


ADDITIONAL_FORM_CONFIGURATION_RESOURCES: Mapping[
    AdditionalFormConfigurationOptions,
    ExportResourceConfig,
] = {
    AdditionalFormConfigurationOptions.product: (ProductResource, "product"),
    AdditionalFormConfigurationOptions.wms_tile_layers: (
        WMSTileLayerResource,
        "wmsTileLayers",
    ),
    AdditionalFormConfigurationOptions.wmts_tile_layers: (
        WMTSTileLayerResource,
        "wmtsTileLayers",
    ),
    AdditionalFormConfigurationOptions.yivi_attribute_groups: (
        YiviAttributeGroupResource,
        "yiviAttributeGroups",
    ),
}


def get_additional_form_configuration_data(
    form: Form, export_options: FormExportOptions
) -> dict[str, JSONObject]:
    """
    Create a dictionary of additional form configuration data for the given form.

    The keys are the names for the export files, and the values are the JSON data
    representing the resource data. This should be used in the form export process, in
    connection with `remove_excluded_additional_configuration_from_form`.
    """
    resources: dict[str, JSONObject] = {}

    options_to_include = set(export_options.additional_form_configuration)
    unknown_options = options_to_include - set(ADDITIONAL_FORM_CONFIGURATION_RESOURCES)

    if unknown_options:
        raise ValueError(
            f"Invalid additional form configuration option(s): {unknown_options}"
        )

    for option, (
        resource,
        output_name,
    ) in ADDITIONAL_FORM_CONFIGURATION_RESOURCES.items():
        if option in options_to_include:
            resources[output_name] = resource().export_for_form(form).export("json")

    return resources
