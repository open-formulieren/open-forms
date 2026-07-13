from dataclasses import dataclass

import tablib

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
from .typing import (
    AdditionalFormConfigurationOptions,
    FormExportOptions,
    FormImportOptions,
)


@dataclass(frozen=True)
class ResourceConfig:
    resource: type[BaseResource]
    output_name: str


ADDITIONAL_FORM_CONFIGURATION_RESOURCES: dict[
    AdditionalFormConfigurationOptions,
    ResourceConfig,
] = {
    AdditionalFormConfigurationOptions.product: ResourceConfig(
        resource=ProductResource,
        output_name="product",
    ),
    AdditionalFormConfigurationOptions.theme: ResourceConfig(
        resource=ThemeResource,
        output_name="theme",
    ),
    AdditionalFormConfigurationOptions.category: ResourceConfig(
        resource=CategoryResource,
        output_name="category",
    ),
    AdditionalFormConfigurationOptions.wms_tile_layers: ResourceConfig(
        resource=WMSTileLayerResource,
        output_name="wmsTileLayers",
    ),
    AdditionalFormConfigurationOptions.wmts_tile_layers: ResourceConfig(
        resource=WMTSTileLayerResource,
        output_name="wmtsTileLayers",
    ),
    AdditionalFormConfigurationOptions.yivi_attribute_groups: ResourceConfig(
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


def import_additional_form_configuration_data(
    resources: JSONObject, import_options: FormImportOptions
):
    if import_options is None:
        return

    selected_options = set(import_options.additional_form_configuration)
    unknown_options = selected_options - set(ADDITIONAL_FORM_CONFIGURATION_RESOURCES)

    if unknown_options:
        raise ValueError(
            f"Invalid additional form configuration option(s): {unknown_options}"
        )

    for option, config in ADDITIONAL_FORM_CONFIGURATION_RESOURCES.items():
        if option in selected_options and config.output_name in resources:
            dataset = tablib.Dataset(resources[config.output_name])
            config.resource().import_data(dataset)
