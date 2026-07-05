from dataclasses import dataclass

from openforms.forms.models import Form
from openforms.typing import JSONObject

from .resources import (
    BaseResource,
    CategoryResource,
    ProductResource,
    ThemeResource,
    WMSTileLayerResource,
    WMTSTileLayerResource,
    YiviAttributeGroupResource,
)
from .typing import AdditionalFormConfigurationOptions, FormExportOptions


@dataclass(frozen=True)
class ExportResourceConfig:
    resource: type[BaseResource]
    output_name: str


ADDITIONAL_FORM_CONFIGURATION_RESOURCES: dict[
    AdditionalFormConfigurationOptions,
    ExportResourceConfig,
] = {
    AdditionalFormConfigurationOptions.product: ExportResourceConfig(
        resource=ProductResource,
        output_name="product",
    ),
    AdditionalFormConfigurationOptions.theme: ExportResourceConfig(
        resource=ThemeResource,
        output_name="theme",
    ),
    AdditionalFormConfigurationOptions.category: ExportResourceConfig(
        resource=CategoryResource,
        output_name="category",
    ),
    AdditionalFormConfigurationOptions.wms_tile_layers: ExportResourceConfig(
        resource=WMSTileLayerResource,
        output_name="wmsTileLayers",
    ),
    AdditionalFormConfigurationOptions.wmts_tile_layers: ExportResourceConfig(
        resource=WMTSTileLayerResource,
        output_name="wmtsTileLayers",
    ),
    AdditionalFormConfigurationOptions.yivi_attribute_groups: ExportResourceConfig(
        resource=YiviAttributeGroupResource,
        output_name="yiviAttributeGroups",
    ),
}


def get_additional_form_configuration_data(
    form: Form, export_options: FormExportOptions
) -> JSONObject:
    """
    Create a dictionary of additional form configuration data for the given form.

    The keys are the names for the export files, and the values are the JSON data
    representing the resource data. This should be used in the form export process, in
    connection with `remove_excluded_additional_configuration_from_form`.
    """
    resources = {}

    selected_options = set(export_options.additional_form_configuration)
    unknown_options = selected_options - set(ADDITIONAL_FORM_CONFIGURATION_RESOURCES)

    if unknown_options:
        raise ValueError(
            f"Invalid additional form configuration option(s): {unknown_options}"
        )

    for option, config in ADDITIONAL_FORM_CONFIGURATION_RESOURCES.items():
        if option in selected_options:
            resources[config.output_name] = config.resource().export_for_form(form).json

    return resources
